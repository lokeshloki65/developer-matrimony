from app import db
from datetime import datetime

def calculate_match_score(user_profile, candidate_profile):
    """Calculate compatibility score between two profiles"""
    score = 0
    max_score = 100
    
    # Age compatibility (20 points)
    user_prefs = user_profile.get('preferences', {})
    age_range = user_prefs.get('ageRange', {'min': 22, 'max': 35})
    candidate_age = calculate_age(candidate_profile.get('dateOfBirth'))
    
    if age_range['min'] <= candidate_age <= age_range['max']:
        score += 20
    
    # Religion/Community match (15 points)
    preferred_religions = user_prefs.get('religions', [])
    if not preferred_religions or candidate_profile.get('religion') in preferred_religions:
        score += 15
    
    # Tech stack overlap (25 points)
    user_tech = set(user_profile.get('developerInfo', {}).get('techStack', []))
    candidate_tech = set(candidate_profile.get('developerInfo', {}).get('techStack', []))
    
    if user_tech and candidate_tech:
        overlap = len(user_tech & candidate_tech)
        tech_score = min(25, (overlap / len(user_tech)) * 25)
        score += tech_score
    
    # Experience level compatibility (15 points)
    user_exp = user_profile.get('developerInfo', {}).get('yearsOfExperience', 0)
    candidate_exp = candidate_profile.get('developerInfo', {}).get('yearsOfExperience', 0)
    
    exp_diff = abs(user_exp - candidate_exp)
    if exp_diff <= 2:
        score += 15
    elif exp_diff <= 5:
        score += 10
    
    # Location proximity (15 points)
    if user_profile.get('city') == candidate_profile.get('city'):
        score += 15
    elif user_profile.get('state') == candidate_profile.get('state'):
        score += 10
    
    # Work type match (10 points)
    preferred_work = user_prefs.get('workPreference')
    if not preferred_work or candidate_profile.get('developerInfo', {}).get('workType') == preferred_work:
        score += 10
    
    return round(score)

def calculate_age(dob_string):
    """Calculate age from date of birth string"""
    try:
        dob = datetime.strptime(dob_string, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except:
        return 0

def find_matches(user_id, limit=20):
    """Find potential matches for a user"""
    try:
        # Get user profile
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return []
        
        user_profile = user_doc.to_dict()
        user_gender = user_profile.get('gender')
        
        # Query for opposite gender (or same if preference set)
        opposite_gender = 'Female' if user_gender == 'Male' else 'Male'
        
        candidates = db.collection('users')\
            .where('gender', '==', opposite_gender)\
            .where('isActive', '==', True)\
            .limit(100)\
            .stream()
        
        matches = []
        for candidate_doc in candidates:
            candidate_id = candidate_doc.id
            
            # Skip self
            if candidate_id == user_id:
                continue
            
            candidate_profile = candidate_doc.to_dict()
            
            # Calculate match score
            score = calculate_match_score(user_profile, candidate_profile)
            
            if score >= 40:  # Minimum threshold
                matches.append({
                    'userId': candidate_id,
                    'profile': candidate_profile,
                    'matchScore': score
                })
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x['matchScore'], reverse=True)
        return matches[:limit]
        
    except Exception as e:
        print(f"Error finding matches: {str(e)}")
        return [] 
