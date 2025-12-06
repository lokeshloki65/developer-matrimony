from functools import wraps
from flask import request, jsonify
from firebase_admin import auth

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "No token provided"}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token.split('Bearer ')[1]
            
            # Verify the token
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token['uid']
            request.user_email = decoded_token.get('email')
            
        except Exception as e:
            return jsonify({"error": "Invalid token", "details": str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check authentication
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "No token provided"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split('Bearer ')[1]
            
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token['uid']
            
            # Check if user is admin
            from app import db
            user_doc = db.collection('users').document(request.user_id).get()
            
            if not user_doc.exists or not user_doc.to_dict().get('isAdmin', False):
                return jsonify({"error": "Admin access required"}), 403
            
        except Exception as e:
            return jsonify({"error": "Unauthorized", "details": str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function 
