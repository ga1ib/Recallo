from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from dotenv import load_dotenv
import os
import logging
from routes import chat, conversations, documents, quiz, topics, notifications, progress
from routes import auth, users, summary, settings, files, health

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB
    UPLOAD_FOLDER='uploads',
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.environ.get("MAIL_USERNAME")
)

# Initialize extensions
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

mail = Mail(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Register blueprints
app.register_blueprint(chat.bp)
app.register_blueprint(conversations.bp)
app.register_blueprint(documents.bp)
app.register_blueprint(quiz.bp)
app.register_blueprint(topics.bp)
app.register_blueprint(notifications.bp)
app.register_blueprint(progress.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(users.bp)
app.register_blueprint(summary.bp)
app.register_blueprint(settings.bp)
app.register_blueprint(files.bp)
app.register_blueprint(health.bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)