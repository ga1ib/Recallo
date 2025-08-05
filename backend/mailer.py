from flask_mail import Mail, Message
from flask import current_app
import logging

mail = Mail()  # Will be initialized from app
_app_instance = None  # Store app reference for use outside request context

def init_mail(app):
    """Initialize Flask-Mail with the app"""
    global _app_instance
    _app_instance = app  # Store app reference

    logging.info("🔧 Initializing Flask-Mail with app config")
    mail.init_app(app)

    # Test the configuration
    with app.app_context():
        try:
            logging.info(f"📧 Mail server: {app.config.get('MAIL_SERVER')}")
            logging.info(f"📧 Mail port: {app.config.get('MAIL_PORT')}")
            logging.info(f"📧 Mail username: {app.config.get('MAIL_USERNAME')}")
            logging.info(f"📧 Mail TLS: {app.config.get('MAIL_USE_TLS')}")
            logging.info("✅ Flask-Mail initialized successfully")
        except Exception as e:
            logging.error(f"❌ Error checking mail config: {e}")

def send_email(to, subject, html):
    """Send email using Flask-Mail within application context"""
    logging.info("📤 Preparing to send email...")
    logging.info(f"📧 To: {to}")
    logging.info(f"📨 Subject: {subject}")

    try:
        # Try to get current app context first
        try:
            app = current_app
        except RuntimeError:
            # No application context, use stored app instance
            app = _app_instance
            if not app:
                logging.error("❌ No Flask application available")
                return False

        # Create application context if needed
        if hasattr(app, 'app_context'):
            with app.app_context():
                msg = Message(
                    subject=subject,
                    recipients=[to],
                    html=html,
                    sender=app.config.get('MAIL_DEFAULT_SENDER')
                )
                logging.info("✉️ Message object created.")
                mail.send(msg)
                logging.info("✅ Email sent successfully.")
                return True
        else:
            # Fallback if app context is not available
            logging.error("❌ Flask app context not available")
            return False

    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False