from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth
from services.cloudinary_service import upload_media
from app import db
from datetime import datetime

bp = Blueprint('profiles', __name__, url_prefix='/api/profiles')

@bp.route('/create', methods=['POST'])
@require_auth
def create_profile():
    try:
        data = request.json
        user_id = request.user_id
        
        profile_data = {
            # Personal Info
            'userId': user_id,
            'fullName': data.get('fullName'),
            'dateOfBirth': data.get('dateOfBirth'),
            'gender': data.get('gender'),
            'religion': data.get('religion'),
            'community': data.get('community'),
            'nativeLanguage': data.get('nativeLanguage', 'English'),
            
            # Location
            'city': data.get('city'),
            'state': data.get('state'),
            'country': data.get('country'),
            
            # Developer Info
            'developerInfo': {
                'role': data.get('role'),
                'yearsOfExperience': data.get('yearsOfExperience'),
                'techStack': data.get('techStack', []),
                'workType': data.get('workType'),
                'companyName': data.get('companyName'),
                'githubUrl': data.get('githubUrl'),
                'linkedinUrl': data.get('linkedinUrl'),
                'portfolioUrl': data.get('portfolioUrl')
            },
            
            # Preferences
            'preferences': {
                'ageRange': data.get('ageRange', {'min': 22, 'max': 35}),
                'religions': data.get('preferredReligions', []),
                'communities': data.get('preferredCommunities', []),
                'techPreferences': data.get('techPreferences', []),
                'workPreference': data.get('workPreference'),
                'locationRadius': data.get('locationRadius', 50)
            },
            
            # Privacy
            'privacy': {
                'hideContact': data.get('hideContact', True),
                'hideLocation': data.get('hideLocation', False),
                'hidePhotos': data.get('hidePhotos', False)
            },
            
            # Verification
            'verification': {
                'emailVerified': False,
                'phoneVerified': False,
                'profileVerified': False,
                'photoVerified': False
            },
            
            # Metadata
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'isActive': True,
            'isPremium': False
        }
        
        # Save to Firestore
        db.collection('users').document(user_id).set(profile_data)
        
        return jsonify({
            "success": True,
            "message": "Profile created successfully",
            "profileId": user_id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/upload-photo', methods=['POST'])
@require_auth
def upload_photo():
    try:
        if 'photo' not in request.files:
            return jsonify({"error": "No photo provided"}), 400
        
        file = request.files['photo']
        user_id = request.user_id
        
        # Upload to Cloudinary
        result = upload_media(file, folder=f"profiles/{user_id}")
        
        # Update user document
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'photos': firestore.ArrayUnion([{
                'url': result['secure_url'],
                'publicId': result['public_id'],
                'uploadedAt': datetime.utcnow()
            }])
        })
        
        return jsonify({
            "success": True,
            "photoUrl": result['secure_url']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<user_id>', methods=['GET'])
@require_auth
def get_profile(user_id):
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            return jsonify({"error": "Profile not found"}), 404
        
        profile = user_doc.to_dict()
        
        # Apply privacy filters if not own profile
        if request.user_id != user_id:
            if profile.get('privacy', {}).get('hideContact'):
                profile.pop('phone', None)
                profile.pop('email', None)
            
            if profile.get('privacy', {}).get('hidePhotos'):
                profile['photos'] = []
        
        return jsonify(profile)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
