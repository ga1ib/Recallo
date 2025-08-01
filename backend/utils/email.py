from flask_mail import Message
from datetime import datetime, timezone, timedelta
import logging
from utils.helpers import supabase

def send_exam_result_email(user_email, user_name, topic_title, score):
    # [Implementation...]
    pass

def has_been_notified_today(user_id, topic_id, notif_type):
    # [Implementation...]
    pass

def record_notification(user_id, topic_id, notif_type, message):
    # [Implementation...]
    pass

def process_notifications():
    # [Implementation...]
    pass