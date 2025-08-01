from flask import Blueprint, request, jsonify, current_app
import logging
import os
from datetime import datetime, timezone, timedelta
from supabase import create_client

# Create blueprint
notifications_bp = Blueprint('notifications', __name__)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper functions for notification preferences
def is_topic_notification_enabled(user_id, topic_id):
    """Return True if user has not disabled notifications for this topic."""
    try:
        resp = supabase.table("user_topic_notification_preferences") \
            .select("enabled") \
            .eq("user_id", user_id) \
            .eq("topic_id", topic_id) \
            .single() \
            .execute()

        if resp.data:
            return resp.data.get("enabled", True)
        else:
            return True  # Default to enabled if no preference found

    except Exception as e:
        logging.error(f"Error checking topic notification preference: {e}")
        return True  # Default to enabled if table doesn't exist

def is_user_email_notification_enabled_global(user_id):
    """Check if user has global email notifications enabled (default: True)"""
    try:
        resp = supabase.table("user_notification_settings") \
            .select("email_notifications_enabled") \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if resp.error or not resp.data:
            return True  # Default to enabled

        return resp.data.get("email_notifications_enabled", True)
    except Exception as e:
        logging.error(f"Error checking global email notification settings: {e}")
        return True

def is_daily_reminders_enabled(user_id):
    """Check if user has daily reminders enabled (default: True)"""
    try:
        resp = supabase.table("user_notification_settings") \
            .select("daily_reminders_enabled") \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if resp.error or not resp.data:
            return True  # Default to enabled

        return resp.data.get("daily_reminders_enabled", True)
    except Exception as e:
        logging.error(f"Error checking daily reminders settings: {e}")
        return True

def has_been_notified_today(user_id, topic_id, notif_type):
    """Avoid duplicate daily/weekly sends."""
    today = datetime.now(timezone.utc).date().isoformat()
    resp = supabase.table("user_notifications") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("topic_id", topic_id) \
        .eq("notification_type", notif_type) \
        .eq("sent_date", today) \
        .limit(1) \
        .execute()
    return bool(resp.data)

def send_email(to, subject, body):
    """Use Flask-Mail to send the message."""
    try:
        from email_utils import send_email as send_email_util
        return send_email_util(to, subject, body)
    except Exception as e:
        current_app.logger.error(f"Mail send failed: {e}")
        return False

def record_notification(user_id, topic_id, notif_type, message):
    """Log the sent notification."""
    now = datetime.now(timezone.utc)
    next_at = now + (timedelta(days=1) if notif_type == "daily" else timedelta(days=7))
    supabase.table("user_notifications").insert({
        "user_id": user_id,
        "topic_id": topic_id,
        "notification_type": notif_type,
        "sent_at": now.isoformat(),
        "sent_date": now.date().isoformat(),
        "next_notification_at": next_at.isoformat(),
        "status": "sent",
        "message": message
    }).execute()

def send_exam_result_email(user_email, user_name, topic_title, score):
    """Send a detailed and friendly result email after quiz submission."""
    subject = f"Your Result for: {topic_title}"

    if score >= 8:
        message = f"""
Hi {user_name},

🎉 Congratulations on your excellent performance!

You scored {score}/10 in the topic: "{topic_title}".

Keep up the great work and continue sharpening your skills. You're doing fantastic!

Best wishes,  
The Recallo Team
"""
    elif score >= 5:
        message = f"""
Hi {user_name},

👍 You scored {score}/10 on the topic: "{topic_title}".

That's a solid effort! With a little more practice, you'll master this topic in no time. Would you like to retake it for a better score?

Stay motivated!  
The Recallo Team
"""
    else:
        message = f"""
Hi {user_name},

💡 You scored {score}/10 on the topic: "{topic_title}".

Don't be discouraged! Every expert was once a beginner. This is your chance to come back stronger — give it another go and improve your score.

We're rooting for you!  
The Recallo Team
"""

    return send_email(user_email, subject, message.strip())

def send_reminder_email(user_email, user_name, title, score, notif_type):
    """Send reminder email based on notification type"""
    try:
        if notif_type == "daily":
            subject = f"Daily Study Reminder: {title}"
            message = f"""
Hi {user_name},

This is your daily reminder to review the topic: "{title}".

Your current score is {score}/10. With consistent practice, you can improve your understanding and achieve mastery!

Keep learning!
The Recallo Team
"""
        else:  # weekly
            subject = f"Weekly Review: {title}"
            message = f"""
Hi {user_name},

Time for your weekly review of: "{title}".

You've mastered this topic with a score of {score}/10. A quick review will help reinforce your knowledge!

Best regards,
The Recallo Team
"""
        
        return send_email(user_email, subject, message.strip())
    except Exception as e:
        logging.error(f"Error sending reminder email: {e}")
        return False

def process_notifications():
    """
    Fetch each user/topic from user_topic_review_features
    and send daily or weekly reminders according to score & preferences.
    """
    try:
        resp = supabase.table("user_topic_review_features").select(
            "user_id, topic_id, title, quiz_score"
        ).execute()

        if not resp.data:
            logging.info("No review features found")
            return
    except Exception as e:
        logging.error(f"Failed to fetch review features: {e}")
        return

    for row in resp.data:
        uid = row["user_id"]
        tid = row["topic_id"]
        title = row["title"]
        score = row["quiz_score"]

        # Check user preferences
        if not is_user_email_notification_enabled_global(uid):
            continue

        if score < 8 and not is_daily_reminders_enabled(uid):
            continue

        if not is_topic_notification_enabled(uid, tid):
            continue

        # Determine notification type
        nt = "daily" if score < 8 else "weekly"

        # Avoid duplicates
        if has_been_notified_today(uid, tid, nt):
            continue

        # Get user info
        try:
            user_resp = supabase.table("users").select("email, name").eq("user_id", uid).single().execute()
            if not user_resp.data:
                logging.error(f"Could not find user email for {uid}")
                continue
        except Exception as e:
            logging.error(f"Error fetching user {uid}: {e}")
            continue

        # Send notification
        user_email = user_resp.data["email"]
        user_name = user_resp.data.get("name", "Learner")

        if send_reminder_email(user_email, user_name, title, score, nt):
            message_body = f"{nt.title()} reminder sent for {title} (score: {score}/10)"
            record_notification(uid, tid, nt, message_body)
            logging.info(f"✅ Sent {nt} reminder to {user_email} for topic: {title}")
        else:
            logging.error(f"❌ Failed to send {nt} reminder to {user_email}")

@notifications_bp.route("/send-exam-email", methods=["POST"])
def send_exam_email():
    """Send exam result email"""
    user_id = request.json.get("user_id")
    topic_id = request.json.get("topic_id")
    score = request.json.get("score")

    topic_resp = supabase.table("topics").select("title").eq("topic_id", topic_id).single().execute()
    user_resp = supabase.table("users").select("email", "name").eq("user_id", user_id).single().execute()

    if topic_resp.data and user_resp.data:
        title = topic_resp.data["title"]
        email = user_resp.data["email"]
        name = user_resp.data["name"] or "Learner"

        success = send_exam_result_email(email, name, title, score)
        return jsonify({"sent": success}), 200
    return jsonify({"error": "Missing user or topic"}), 400

@notifications_bp.route("/api/run-notifications", methods=["POST"])
def run_notifications_route():
    """Trigger notification processing (protect this route in production!)"""
    process_notifications()
    return jsonify({"message": "Notifications processed"}), 200

@notifications_bp.route("/api/notification-settings/<user_id>", methods=["GET"])
def get_notification_settings(user_id):
    """Get user's notification preferences"""
    try:
        # Default settings
        global_settings = {
            "email_notifications_enabled": True,
            "daily_reminders_enabled": True
        }
        topic_settings = {}

        # Get global settings
        try:
            global_resp = supabase.table("user_notification_settings") \
                .select("email_notifications_enabled, daily_reminders_enabled") \
                .eq("user_id", user_id) \
                .execute()

            if global_resp.data and len(global_resp.data) > 0:
                global_settings.update(global_resp.data[0])
        except Exception as e:
            logging.info(f"No global notification settings found for user {user_id}: {e}")

        # Get topic-specific settings
        try:
            topic_resp = supabase.table("user_topic_notification_preferences") \
                .select("topic_id, enabled") \
                .eq("user_id", user_id) \
                .execute()

            if topic_resp.data:
                for item in topic_resp.data:
                    topic_settings[item["topic_id"]] = item["enabled"]
        except Exception as e:
            logging.info(f"No topic notification settings found for user {user_id}: {e}")

        return jsonify({
            "global_settings": global_settings,
            "topic_settings": topic_settings
        }), 200

    except Exception as e:
        logging.error(f"Error fetching notification settings: {e}")
        return jsonify({
            "global_settings": {
                "email_notifications_enabled": True,
                "daily_reminders_enabled": True
            },
            "topic_settings": {}
        }), 200

@notifications_bp.route("/api/notification-settings/<user_id>", methods=["PUT"])
def update_notification_settings(user_id):
    """Update user's notification preferences"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        global_settings = data.get("global_settings", {})
        topic_settings = data.get("topic_settings", {})

        # Update global settings
        if global_settings:
            try:
                existing_resp = supabase.table("user_notification_settings") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .execute()

                settings_data = {
                    "user_id": user_id,
                    "email_notifications_enabled": global_settings.get("email_notifications_enabled", True),
                    "daily_reminders_enabled": global_settings.get("daily_reminders_enabled", True),
                    "updated_at": datetime.now().isoformat()
                }

                if existing_resp.data and len(existing_resp.data) > 0:
                    supabase.table("user_notification_settings") \
                        .update(settings_data) \
                        .eq("user_id", user_id) \
                        .execute()
                else:
                    supabase.table("user_notification_settings") \
                        .insert(settings_data) \
                        .execute()
            except Exception as e:
                logging.error(f"Error updating global settings: {e}")

        # Update topic-specific settings
        for topic_id, enabled in topic_settings.items():
            try:
                existing_topic_resp = supabase.table("user_topic_notification_preferences") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .eq("topic_id", topic_id) \
                    .execute()

                topic_data = {
                    "user_id": user_id,
                    "topic_id": topic_id,
                    "enabled": enabled,
                    "updated_at": datetime.now().isoformat()
                }

                if existing_topic_resp.data and len(existing_topic_resp.data) > 0:
                    supabase.table("user_topic_notification_preferences") \
                        .update(topic_data) \
                        .eq("user_id", user_id) \
                        .eq("topic_id", topic_id) \
                        .execute()
                else:
                    supabase.table("user_topic_notification_preferences") \
                        .insert(topic_data) \
                        .execute()
            except Exception as e:
                logging.error(f"Error updating topic setting for {topic_id}: {e}")

        return jsonify({"message": "Notification settings updated successfully"}), 200

    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return jsonify({"error": "Failed to update notification settings"}), 500