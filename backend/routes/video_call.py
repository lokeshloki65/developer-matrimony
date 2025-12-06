from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth
from app import db
from datetime import datetime
import secrets

bp = Blueprint('video_call', __name__, url_prefix='/api/video-call')

@bp.route('/create-room', methods=['POST'])
@require_auth
def create_room():
    """Create a video call room"""
    try:
        data = request.json
        participant_id = data.get('participantId')
        
        if not participant_id:
            return jsonify({"error": "Participant required"}), 400
        
        # Check if users have matched
        match_exists = db.collection('matches')\
            .where('senderId', 'in', [request.user_id, participant_id])\
            .where('receiverId', 'in', [request.user_id, participant_id])\
            .where('status', '==', 'accepted')\
            .limit(1)\
            .get()
        
        if not match_exists:
            return jsonify({"error": "Can only call matched users"}), 403
        
        # Generate room ID
        room_id = secrets.token_urlsafe(16)
        
        # Create room
        room_data = {
            'roomId': room_id,
            'createdBy': request.user_id,
            'participants': [request.user_id, participant_id],
            'status': 'waiting',
            'createdAt': datetime.utcnow()
        }
        
        db.collection('video_rooms').document(room_id).set(room_data)
        
        # Notify participant
        db.collection('notifications').add({
            'userId': participant_id,
            'type': 'video_call',
            'title': 'Incoming Video Call',
            'message': 'Someone is calling you',
            'roomId': room_id,
            'read': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "roomId": room_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/join-room/<room_id>', methods=['POST'])
@require_auth
def join_room(room_id):
    """Join a video call room"""
    try:
        room_ref = db.collection('video_rooms').document(room_id)
        room_doc = room_ref.get()
        
        if not room_doc.exists:
            return jsonify({"error": "Room not found"}), 404
        
        room_data = room_doc.to_dict()
        
        # Verify user is participant
        if request.user_id not in room_data['participants']:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update room status
        room_ref.update({
            'status': 'active',
            'joinedAt': datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "room": room_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/end-call/<room_id>', methods=['POST'])
@require_auth
def end_call(room_id):
    """End a video call"""
    try:
        room_ref = db.collection('video_rooms').document(room_id)
        room_ref.update({
            'status': 'ended',
            'endedAt': datetime.utcnow(),
            'endedBy': request.user_id
        })
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500