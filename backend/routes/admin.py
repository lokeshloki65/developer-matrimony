from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_admin
from app import db
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/dashboard', methods=['GET'])
@require_admin
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        # Total users
        total_users = len(list(db.collection('users').stream()))
        
        # Active users (logged in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = db.collection('users')\
            .where('lastLoginAt', '>=', thirty_days_ago)\
            .stream()
        active_count = len(list(active_users))
        
        # Pending verifications
        pending_verifications = db.collection('users')\
            .where('verification.profileVerified', '==', False)\
            .stream()
        pending_count = len(list(pending_verifications))
        
        # Total matches
        total_matches = len(list(db.collection('matches').stream()))
        
        # Active conversations
        active_conversations = db.collection('conversations')\
            .where('lastMessageAt', '>=', thirty_days_ago)\
            .stream()
        active_conv_count = len(list(active_conversations))
        
        # Pending reports
        pending_reports = db.collection('reports')\
            .where('status', '==', 'pending')\
            .stream()
        pending_reports_count = len(list(pending_reports))
        
        # Premium users
        premium_users = db.collection('users')\
            .where('isPremium', '==', True)\
            .stream()
        premium_count = len(list(premium_users))
        
        return jsonify({
            "success": True,
            "stats": {
                "totalUsers": total_users,
                "activeUsers": active_count,
                "pendingVerifications": pending_count,
                "totalMatches": total_matches,
                "activeConversations": active_conv_count,
                "pendingReports": pending_reports_count,
                "premiumUsers": premium_count
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get all users with filters"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        filter_type = request.args.get('filter', 'all')
        
        query = db.collection('users')
        
        # Apply filters
        if filter_type == 'verified':
            query = query.where('verification.profileVerified', '==', True)
        elif filter_type == 'unverified':
            query = query.where('verification.profileVerified', '==', False)
        elif filter_type == 'premium':
            query = query.where('isPremium', '==', True)
        
        # Get users
        users = query.limit(limit).stream()
        
        result = []
        for user in users:
            user_data = user.to_dict()
            user_data['id'] = user.id
            result.append(user_data)
        
        return jsonify({
            "success": True,
            "users": result,
            "page": page,
            "limit": limit
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/verify-user/<user_id>', methods=['POST'])
@require_admin
def verify_user(user_id):
    """Verify a user profile"""
    try:
        data = request.json
        verification_type = data.get('type')  # profile, photo, phone
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404
        
        # Update verification status
        update_data = {}
        if verification_type == 'profile':
            update_data['verification.profileVerified'] = True
        elif verification_type == 'photo':
            update_data['verification.photoVerified'] = True
        elif verification_type == 'phone':
            update_data['verification.phoneVerified'] = True
        
        update_data['verifiedAt'] = datetime.utcnow()
        update_data['verifiedBy'] = request.user_id
        
        user_ref.update(update_data)
        
        # Send notification to user
        db.collection('notifications').add({
            'userId': user_id,
            'type': 'verification_approved',
            'title': 'Profile Verified',
            'message': f'Your {verification_type} has been verified!',
            'read': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({"success": True, "message": "User verified successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/reports', methods=['GET'])
@require_admin
def get_reports():
    """Get all user reports"""
    try:
        status = request.args.get('status', 'pending')
        
        reports = db.collection('reports')\
            .where('status', '==', status)\
            .order_by('createdAt', direction='DESCENDING')\
            .stream()
        
        result = []
        for report in reports:
            report_data = report.to_dict()
            report_data['id'] = report.id
            
            # Get reporter and reported user info
            reporter = db.collection('users').document(report_data['reporterId']).get()
            reported = db.collection('users').document(report_data['reportedId']).get()
            
            if reporter.exists:
                report_data['reporter'] = {
                    'id': report_data['reporterId'],
                    'name': reporter.to_dict().get('fullName')
                }
            
            if reported.exists:
                report_data['reported'] = {
                    'id': report_data['reportedId'],
                    'name': reported.to_dict().get('fullName')
                }
            
            result.append(report_data)
        
        return jsonify({"success": True, "reports": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/reports/<report_id>/resolve', methods=['POST'])
@require_admin
def resolve_report(report_id):
    """Resolve a user report"""
    try:
        data = request.json
        action = data.get('action')  # dismiss, warn, suspend, ban
        
        report_ref = db.collection('reports').document(report_id)
        report_doc = report_ref.get()
        
        if not report_doc.exists:
            return jsonify({"error": "Report not found"}), 404
        
        report_data = report_doc.to_dict()
        reported_user_id = report_data['reportedId']
        
        # Update report status
        report_ref.update({
            'status': 'resolved',
            'action': action,
            'resolvedBy': request.user_id,
            'resolvedAt': datetime.utcnow(),
            'notes': data.get('notes', '')
        })
        
        # Take action on reported user
        if action in ['suspend', 'ban']:
            db.collection('users').document(reported_user_id).update({
                'isActive': False,
                'suspendedAt': datetime.utcnow(),
                'suspensionReason': report_data.get('reason')
            })
            
            # Notify user
            db.collection('notifications').add({
                'userId': reported_user_id,
                'type': 'account_suspended',
                'title': 'Account Suspended',
                'message': f'Your account has been {action}ed due to policy violation.',
                'read': False,
                'createdAt': datetime.utcnow()
            })
        
        return jsonify({"success": True, "message": "Report resolved successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/featured-profiles', methods=['POST'])
@require_admin
def set_featured_profile():
    """Set a profile as featured"""
    try:
        data = request.json
        user_id = data.get('userId')
        is_featured = data.get('isFeatured', True)
        
        db.collection('users').document(user_id).update({
            'isFeatured': is_featured,
            'featuredAt': datetime.utcnow() if is_featured else None
        })
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/broadcast', methods=['POST'])
@require_admin
def broadcast_notification():
    """Send notification to all users or filtered group"""
    try:
        data = request.json
        title = data.get('title')
        message = data.get('message')
        user_filter = data.get('filter', 'all')  # all, premium, verified
        
        # Get target users
        query = db.collection('users')
        
        if user_filter == 'premium':
            query = query.where('isPremium', '==', True)
        elif user_filter == 'verified':
            query = query.where('verification.profileVerified', '==', True)
        
        users = query.stream()
        
        # Create notifications
        batch = db.batch()
        notification_count = 0
        
        for user in users:
            notification_ref = db.collection('notifications').document()
            batch.set(notification_ref, {
                'userId': user.id,
                'type': 'broadcast',
                'title': title,
                'message': message,
                'read': False,
                'createdAt': datetime.utcnow()
            })
            notification_count += 1
            
            # Commit in batches of 500 (Firestore limit)
            if notification_count % 500 == 0:
                batch.commit()
                batch = db.batch()
        
        # Commit remaining
        if notification_count % 500 != 0:
            batch.commit()
        
        return jsonify({
            "success": True,
            "message": f"Notification sent to {notification_count} users"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
