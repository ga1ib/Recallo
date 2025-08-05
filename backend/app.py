from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from supabase import create_client
from dotenv import load_dotenv
from mailer import  init_mail
import os
import logging

# Third-party scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
import atexit

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# Import notifications blueprint and process function
try:
    from routes.notifications import notifications_bp, process_notifications
    notifications_enabled = True
except ImportError as e:
    notifications_enabled = False
    logging.error(f"Failed to import notifications module: {e}")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# App configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
app.config['UPLOAD_FOLDER'] = 'uploads'

# Setup Flask-Mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=GMAIL_USER,
    MAIL_PASSWORD=GMAIL_PASS,
    MAIL_DEFAULT_SENDER=GMAIL_USER,
)

init_mail(app)
# Initialize extensions
# mail = Mail(app)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app.config['supabase'] = supabase

# CORS configuration
CORS(app, resources={
    r"/chat": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/upload": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/ask": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/quiz-question": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/generate-questions": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/submit-answers": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/api/*": {"origins": ["http://localhost:5000", "http://localhost:5173"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]},
    r"/*": {"origins": "*"}
}, supports_credentials=True)

# Blueprint registration with individual error handling
blueprints = [
    ('routes.conversations', 'conversations_bp'),
    ('routes.chat', 'chat_bp'),
    ('routes.documents', 'documents_bp'),
    ('routes.quiz', 'quiz_bp'),
    ('routes.notifications', 'notifications_bp'),
    ('routes.generate_flashcards', 'generate_flashcards_bp'),  # Added missing flashcards blueprint
    ('routes.topics', 'bp'),  # Using 'bp' for topics
    ('routes.settings', 'bp'),  # Using 'bp' for settings
    ('routes.users', 'users_bp'),
    ('routes.files', 'files_bp'),
    ('routes.progress', 'progress_bp'),
    ('routes.summary', 'summary_bp'),
    ('routes.health', 'health_bp'),
    ('routes.extensions', 'extensions_bp'),
]

for module_path, bp_name in blueprints:
    try:
        module = __import__(module_path, fromlist=[bp_name])
        bp = getattr(module, bp_name)
        app.register_blueprint(bp)
        logging.info(f"Registered blueprint: {bp_name} from {module_path}")
    except (ImportError, AttributeError) as e:
        logging.error(f"Failed to register {bp_name} from {module_path}: {e}")

# Scheduler setup for daily reminders
if notifications_enabled:
    scheduler = BackgroundScheduler()
    dhaka_tz = pytz.timezone("Asia/Dhaka")
    
    def daily_reminder_job():
        app.logger.info(f"[{datetime.now(dhaka_tz)}] Running daily notifications...")
        process_notifications()
    
    # Schedule at 10:00 AM Dhaka time every day
    scheduler.add_job(
        func=daily_reminder_job,
        trigger='cron',
        hour=10,
        minute=0,
        timezone=dhaka_tz,
        id='daily_reminder_job'
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

# Root route
@app.route("/")
def index():
    return jsonify({
        "message": "Recallo API is running!",
        "version": "1.0.0",
        "status": "healthy"
    })

# Health check route
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Recallo Backend API"
    })



# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Run the app
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)