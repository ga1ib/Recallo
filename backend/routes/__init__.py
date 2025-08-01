from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # App configuration
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Flask-Mail Configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME")
    
    # Initialize extensions
    mail.init_app(app)
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # CORS configuration
    CORS(app, resources={
        r"/chat": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
        r"/upload": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
        r"/ask": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
        r"/quiz-question": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
        r"/generate-questions": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
        r"/submit-answers": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
        r"/api/progress/.*": {"origins": "http://localhost:5173", "methods": ["GET", "OPTIONS"]},
        r"/api/answer-analysis": {"origins": "http://localhost:5173", "methods": ["GET", "OPTIONS"]},
        r"/*": {"origins": "*"}
    }, supports_credentials=True)
    
    # Register blueprints
    from .conversations import conversations_bp
    from .chat import chat_bp
    from .documents import documents_bp
    from .quiz import quiz_bp
    from .notifications import notifications_bp
    from .topics import topics_bp
    
    app.register_blueprint(conversations_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(topics_bp)
    
    return app