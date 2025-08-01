from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from supabase import create_client
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
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
mail = Mail(app)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Make supabase available globally
app.config['supabase'] = supabase

# CORS configuration
CORS(app, resources={
    r"/chat": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/upload": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/ask": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/quiz-question": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/generate-questions": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/submit-answers": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["POST", "OPTIONS"]},
    r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]},
    r"/*": {"origins": "*"}
}, supports_credentials=True)

# Import and register blueprints
try:
    from routes.conversations import conversations_bp
    app.register_blueprint(conversations_bp)
    logging.info("Registered conversations blueprint")
except ImportError as e:
    logging.error(f"Failed to import conversations blueprint: {e}")

try:
    from routes.chat import chat_bp
    app.register_blueprint(chat_bp)
    logging.info("Registered chat blueprint")
except ImportError as e:
    logging.error(f"Failed to import chat blueprint: {e}")

try:
    from routes.documents import documents_bp
    app.register_blueprint(documents_bp)
    logging.info("Registered documents blueprint")
except ImportError as e:
    logging.error(f"Failed to import documents blueprint: {e}")

try:
    from routes.quiz import quiz_bp
    app.register_blueprint(quiz_bp)
    logging.info("Registered quiz blueprint")
except ImportError as e:
    logging.error(f"Failed to import quiz blueprint: {e}")

try:
    from routes.notifications import notifications_bp
    app.register_blueprint(notifications_bp)
    logging.info("Registered notifications blueprint")
except ImportError as e:
    logging.error(f"Failed to import notifications blueprint: {e}")

try:
    from routes.topics import bp as topics_bp
    app.register_blueprint(topics_bp)
    logging.info("Registered topics blueprint")
except ImportError as e:
    logging.error(f"Failed to import topics blueprint: {e}")

try:
    from routes.settings import bp as settings_bp
    app.register_blueprint(settings_bp)
    logging.info("Registered settings blueprint")
except ImportError as e:
    logging.error(f"Failed to import settings blueprint: {e}")

try:
    from routes.users import users_bp
    app.register_blueprint(users_bp)
    logging.info("Registered users blueprint")
except ImportError as e:
    logging.error(f"Failed to import users blueprint: {e}")

# Auth blueprint temporarily disabled due to import issues
# try:
#     from routes.auth import auth_bp
#     app.register_blueprint(auth_bp)
#     logging.info("Registered auth blueprint")
# except ImportError as e:
#     logging.error(f"Failed to import auth blueprint: {e}")

try:
    from routes.files import files_bp
    app.register_blueprint(files_bp)
    logging.info("Registered files blueprint")
except ImportError as e:
    logging.error(f"Failed to import files blueprint: {e}")

try:
    from routes.progress import progress_bp
    app.register_blueprint(progress_bp)
    logging.info("Registered progress blueprint")
except ImportError as e:
    logging.error(f"Failed to import progress blueprint: {e}")

try:
    from routes.summary import summary_bp
    app.register_blueprint(summary_bp)
    logging.info("Registered summary blueprint")
except ImportError as e:
    logging.error(f"Failed to import summary blueprint: {e}")

try:
    from routes.health import health_bp
    app.register_blueprint(health_bp)
    logging.info("Registered health blueprint")
except ImportError as e:
    logging.error(f"Failed to import health blueprint: {e}")

try:
    from routes.extensions import extensions_bp
    app.register_blueprint(extensions_bp)
    logging.info("Registered extensions blueprint")
except ImportError as e:
    logging.error(f"Failed to import extensions blueprint: {e}")

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
        "timestamp": "2025-08-01",
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
