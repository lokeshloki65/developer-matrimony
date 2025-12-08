from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary 
from config import Config
 
app = Flask(__name__)
app.config.from_object(Config)
CORS(app) 

# Initialize Firebase
cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Cloudinary
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

# Import routes
from routes import auth, profiles, matches, chat, admin

app.register_blueprint(auth.bp)
app.register_blueprint(profiles.bp)
app.register_blueprint(matches.bp)
app.register_blueprint(chat.bp)
app.register_blueprint(admin.bp)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0"})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 



