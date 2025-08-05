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

# Temporary in-memory storage for notification settings (until tables are created)
_notification_settings = {}

# Helper functions for notification preferences
def is_topic_notification_enabled(user_id, topic_id):
    # For now, default to enabled since the preferences table doesn't exist
    # This can be changed later when the preferences table is created
    return True

def is_user_email_notification_enabled_global(user_id):
    # For now, default to enabled since the settings table doesn't exist
    # This can be changed later when the settings table is created
    return True

def is_daily_reminders_enabled(user_id):
    # For now, default to enabled since the settings table doesn't exist
    # This can be changed later when the settings table is created
    return True

def has_been_notified_today(user_id, topic_id, notif_type):
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
    try:
        from email_utils import send_email as send_email_util
        return send_email_util(to, subject, body)
    except Exception as e:
        current_app.logger.error(f"Mail send failed: {e}")
        return False

def record_notification(user_id, topic_id, notif_type, message):
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
    subject = f"Your Result for: {topic_title}"
    if score >= 8:
        message = f"""
Hi {user_name},

🎉 Congratulations on your excellent performance!

You scored {score}/10 in the topic: \"{topic_title}\".

Keep up the great work and continue sharpening your skills. You're doing fantastic!

Best wishes,  
The Recallo Team
"""
    elif score >= 5:
        message = f"""
Hi {user_name},

👍 You scored {score}/10 on the topic: \"{topic_title}\".

That's a solid effort! With a little more practice, you'll master this topic in no time. Would you like to retake it for a better score?

Stay motivated!  
The Recallo Team
"""
    else:
        message = f"""
Hi {user_name},

💡 You scored {score}/10 on the topic: \"{topic_title}\".

Don't be discouraged! Every expert was once a beginner. This is your chance to come back stronger — give it another go and improve your score.

We're rooting for you!  
The Recallo Team
"""
    return send_email(user_email, subject, message.strip())

def send_reminder_email(user_email, user_name, title, score, notif_type):
    try:
        if notif_type == "daily":
            subject = f"Daily Study Reminder: {title}"
            message = f"""
Hi {user_name},

This is your daily reminder to review the topic: \"{title}\".

Your current score is {score}/10. With consistent practice, you can improve your understanding and achieve mastery!

Keep learning!
The Recallo Team
"""
        else:
            subject = f"Weekly Review: {title}"
            message = f"""
Hi {user_name},

Time for your weekly review of: \"{title}\".

You've mastered this topic with a score of {score}/10. A quick review will help reinforce your knowledge!

Best regards,
The Recallo Team
"""
        return send_email(user_email, subject, message.strip())
    except Exception as e:
        logging.error(f"Error sending reminder email: {e}")
        return False

def process_notifications():
    try:
        resp = supabase.table("user_topic_review_features").select(
            "user_id, topic_id, title, latest_score"
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
        score = row["latest_score"]

        # Skip if score is null or invalid
        if score is None:
            logging.info(f"Skipped {uid}/{tid} — no score available")
            continue

        nt = "daily" if score < 8 else "weekly"

        if not is_user_email_notification_enabled_global(uid):
            logging.info(f"Skipped {uid} — global notifications disabled")
            continue
        if score < 8 and not is_daily_reminders_enabled(uid):
            logging.info(f"Skipped {uid}/{tid} — daily reminders off for low score {score}")
            continue
        if not is_topic_notification_enabled(uid, tid):
            logging.info(f"Skipped {uid}/{tid} — topic notification off")
            continue
        if has_been_notified_today(uid, tid, nt):
            logging.info(f"Skipped {uid}/{tid} — already notified today ({nt})")
            continue

        try:
            user_resp = supabase.table("users").select("email, name").eq("user_id", uid).execute()
            if not user_resp.data or len(user_resp.data) == 0:
                logging.info(f"Could not find user email for {uid} - user may not exist in users table")
                continue
        except Exception as e:
            logging.info(f"Error fetching user {uid}: {e}")
            continue

        user_email = user_resp.data[0]["email"]
        user_name = user_resp.data[0].get("name", "Learner")

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
        # Use in-memory storage as fallback
        user_settings = _notification_settings.get(user_id, {
            "global_settings": {
                "email_notifications_enabled": True,
                "daily_reminders_enabled": True
            },
            "topic_settings": {}
        })

        logging.info(f"📥 GET notification settings for user {user_id}: {user_settings}")
        return jsonify(user_settings), 200

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
    logging.info(f"🔧 PUT /api/notification-settings/{user_id} called")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        logging.info(f"📤 Updating settings for user {user_id}: {data}")

        # Store in memory (temporary solution)
        _notification_settings[user_id] = {
            "global_settings": data.get("global_settings", {
                "email_notifications_enabled": True,
                "daily_reminders_enabled": True
            }),
            "topic_settings": data.get("topic_settings", {})
        }

        logging.info(f"✅ Settings updated in memory for user {user_id}")
        return jsonify({"message": "Notification settings updated successfully"}), 200

    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return jsonify({"error": "Failed to update notification settings"}), 500