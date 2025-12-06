import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

class GeminiChatbot:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.system_prompt = """
        You are a helpful assistant for a Developer Matrimony Platform.
        Your role is to:
        1. Help users create and optimize their profiles
        2. Suggest compatible matches based on tech stack and preferences
        3. Generate ice-breaker messages for conversations
        4. Answer FAQs about the platform
        5. Detect Tamil language input and respond in Tamil when appropriate
        
        Be friendly, professional, and culturally sensitive.
        For technical queries, escalate to admin if needed.
        """
    
    def chat(self, user_message, language='en', context=None):
        """Generate AI response"""
        try:
            # Build full prompt
            full_prompt = f"{self.system_prompt}\n\n"
            
            if language == 'ta':
                full_prompt += "Please respond in Tamil (தமிழ்) language.\n\n"
            
            if context:
                full_prompt += f"Context: {context}\n\n"
            
            full_prompt += f"User: {user_message}\n\nAssistant:"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            return {
                "success": True,
                "response": response.text,
                "language": language
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I'm having trouble processing that. Please contact support."
            }
    
    def suggest_icebreaker(self, user_profile, match_profile):
        """Generate personalized ice-breaker message"""
        try:
            common_tech = set(user_profile.get('developerInfo', {}).get('techStack', [])) & \
                         set(match_profile.get('developerInfo', {}).get('techStack', []))
            
            prompt = f"""
            Generate a friendly, professional ice-breaker message for a developer matrimony match.
            
            Common tech interests: {', '.join(common_tech) if common_tech else 'None'}
            Match's role: {match_profile.get('developerInfo', {}).get('role')}
            
            The message should be:
            - Professional yet warm
            - Reference common interests if any
            - Be culturally appropriate for matrimony context
            - Max 2-3 sentences
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return "Hi! I noticed we have similar professional interests. Would love to connect and know more about you."

chatbot = GeminiChatbot() 
