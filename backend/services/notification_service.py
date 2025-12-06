from firebase_admin import messaging
from app import db

def send_push_notification(user_id, title, body, data=None):
    """Send push notification to user"""
    try:
        # Get user's FCM token
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()
        fcm_token = user_data.get('fcmToken')
        
        if not fcm_token:
            return False
        
        # Create message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=fcm_token
        )
        
        # Send message
        response = messaging.send(message)
        print(f'Successfully sent notification: {response}')
        return True
        
    except Exception as e:
        print(f'Error sending notification: {str(e)}')
        return False

def send_multicast_notification(user_ids, title, body, data=None):
    """Send notification to multiple users"""
    try:
        # Get FCM tokens
        tokens = []
        for user_id in user_ids:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                token = user_doc.to_dict().get('fcmToken')
                if token:
                    tokens.append(token)
        
        if not tokens:
            return False
        
        # Create multicast message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            tokens=tokens
        )
        
        # Send message
        response = messaging.send_multicast(message)
        print(f'Successfully sent {response.success_count} notifications')
        return True
        
    except Exception as e:
        print(f'Error sending multicast notification: {str(e)}')
        return False