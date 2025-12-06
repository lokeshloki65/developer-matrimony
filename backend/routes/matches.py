from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth
from services.matching_service import find_matches
from app import db
from datetime import datetime

bp = Blueprint('matches', __name__, url_prefix='/api/matches')

@bp.route('/discover', methods=['GET'])
@require_auth
def discover_matches():
    try:
        user_id = request.user_id
        limit = request.args.get('limit', 20, type=int)
        
        matches = find_matches(user_id, limit)
        
        return jsonify({
            "success": True,
            "matches": matches,
            "count": len(matches)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/send-request', methods=['POST'])
@require_auth
def send_match_request():
    try:
        data = request.json
        sender_id = request.user_id
        receiver_id = data.get('receiverId')
        
        if not receiver_id:
            return jsonify({"error": "Receiver ID required"}), 400
        
        # Check if request already exists
        existing = db.collection('matches')\
            .where('senderId', '==', sender_id)\
            .where('receiverId', '==', receiver_id)\
            .limit(1)\
            .get()
        
        if existing:
            return jsonify({"error": "Request already sent"}), 400
        
        # Create match request
        match_data = {
            'senderId': sender_id,
            'receiverId': receiver_id,
            'status': 'pending',  # pending, accepted, rejected
            'message': data.get('message', ''),
            'createdAt': datetime.utcnow()
        }
        
        match_ref = db.collection('matches').add(match_data)
        
        # Create notification for receiver
        db.collection('notifications').add({
            'userId': receiver_id,
            'type': 'match_request',
            'title': 'New Match Request',
            'message': 'Someone is interested in your profile',
            'matchId': match_ref[1].id,
            'read': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "matchId": match_ref[1].id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/respond', methods=['POST'])
@require_auth
def respond_to_request():
    try:
        data = request.json
        match_id = data.get('matchId')
        action = data.get('action')  # accept or reject
        
        if action not in ['accept', 'reject']:
            return jsonify({"error": "Invalid action"}), 400
        
        match_ref = db.collection('matches').document(match_id)
        match_doc = match_ref.get()
        
        if not match_doc.exists:
            return jsonify({"error": "Match request not found"}), 404
        
        match_data = match_doc.to_dict()
        
        # Verify user is the receiver
        if match_data['receiverId'] != request.user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update status
        match_ref.update({
            'status': 'accepted' if action == 'accept' else 'rejected',
            'respondedAt': datetime.utcnow()
        })
        
        # Notify sender
        db.collection('notifications').add({
            'userId': match_data['senderId'],
            'type': 'match_response',
            'title': f'Match Request {action.capitalize()}ed',
            'message': f'Your request was {action}ed',
            'matchId': match_id,
            'read': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500