from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth
from app import db
from datetime import datetime
import uuid

bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@bp.route('/conversations', methods=['GET'])
@require_auth
def get_conversations():
    """Get all conversations for current user"""
    try:
        user_id = request.user_id
        
        # Get conversations where user is a participant
        conversations = db.collection('conversations')\
            .where('participants', 'array_contains', user_id)\
            .order_by('lastMessageAt', direction='DESCENDING')\
            .stream()
        
        result = []
        for conv in conversations:
            conv_data = conv.to_dict()
            conv_data['id'] = conv.id
            
            # Get other participant's info
            other_user_id = [p for p in conv_data['participants'] if p != user_id][0]
            other_user = db.collection('users').document(other_user_id).get()
            
            if other_user.exists:
                other_user_data = other_user.to_dict()
                conv_data['otherUser'] = {
                    'userId': other_user_id,
                    'fullName': other_user_data.get('fullName'),
                    'photo': other_user_data.get('photos', [{}])[0].get('url') if other_user_data.get('photos') else None
                }
            
            result.append(conv_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/send-message', methods=['POST'])
@require_auth
def send_message():
    """Send a message in a conversation"""
    try:
        data = request.json
        sender_id = request.user_id
        receiver_id = data.get('receiverId')
        message_text = data.get('message')
        
        if not all([receiver_id, message_text]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Find or create conversation
        conv_id = get_or_create_conversation(sender_id, receiver_id)
        
        # Create message
        message_data = {
            'conversationId': conv_id,
            'senderId': sender_id,
            'receiverId': receiver_id,
            'text': message_text,
            'type': 'text',
            'read': False,
            'createdAt': datetime.utcnow()
        }
        
        message_ref = db.collection('messages').add(message_data)
        
        # Update conversation
        db.collection('conversations').document(conv_id).update({
            'lastMessage': message_text,
            'lastMessageAt': datetime.utcnow(),
            f'unreadCount.{receiver_id}': firestore.Increment(1)
        })
        
        # Send notification
        db.collection('notifications').add({
            'userId': receiver_id,
            'type': 'new_message',
            'title': 'New Message',
            'message': message_text[:50],
            'senderId': sender_id,
            'read': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "messageId": message_ref[1].id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_or_create_conversation(user1_id, user2_id):
    """Find existing conversation or create new one"""
    # Create consistent participant list
    participants = sorted([user1_id, user2_id])
    
    # Check if conversation exists
    existing = db.collection('conversations')\
        .where('participants', '==', participants)\
        .limit(1)\
        .get()
    
    if existing:
        return existing[0].id
    
    # Create new conversation
    conv_data = {
        'participants': participants,
        'createdAt': datetime.utcnow(),
        'lastMessage': '',
        'lastMessageAt': datetime.utcnow(),
        'unreadCount': {user1_id: 0, user2_id: 0}
    }
    
    conv_ref = db.collection('conversations').add(conv_data)
    return conv_ref[1].id

@bp.route('/messages/<conversation_id>', methods=['GET'])
@require_auth
def get_messages(conversation_id):
    """Get all messages in a conversation"""
    try:
        user_id = request.user_id
        
        # Verify user is participant
        conv_doc = db.collection('conversations').document(conversation_id).get()
        if not conv_doc.exists:
            return jsonify({"error": "Conversation not found"}), 404
        
        conv_data = conv_doc.to_dict()
        if user_id not in conv_data['participants']:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Get messages
        messages = db.collection('messages')\
            .where('conversationId', '==', conversation_id)\
            .order_by('createdAt', direction='ASCENDING')\
            .stream()
        
        result = []
        for msg in messages:
            msg_data = msg.to_dict()
            msg_data['id'] = msg.id
            msg_data['createdAt'] = msg_data['createdAt'].isoformat()
            result.append(msg_data)
        
        # Mark messages as read
        db.collection('conversations').document(conversation_id).update({
            f'unreadCount.{user_id}': 0
        })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
