from flask import Blueprint, jsonify, request
import logging
from supabase import create_client
import os

bp = Blueprint('topics', __name__, url_prefix='/api/topics')

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@bp.route('/<user_id>', methods=['GET'])
def get_user_topics(user_id):
    try:
        topics_resp = supabase.table("topics").select(
            "topic_id, title, created_at"
        ).eq("user_id", user_id).execute()

        if not topics_resp.data:
            return jsonify([]), 200

        topics_with_status = []
        for topic in topics_resp.data:
            topic_id = topic["topic_id"]
            attempt_resp = supabase.table("quiz_attempts").select(
                "score"
            ).eq("user_id", user_id).eq("topic_id", topic_id).order(
                "submitted_at", desc=True
            ).limit(1).execute()

            if attempt_resp.data:
                latest_score = attempt_resp.data[0]["score"]
                if latest_score >= 8:
                    topic_status = "Completed"
                elif latest_score >= 5:
                    topic_status = "Weak"
                else:
                    topic_status = "Not"
            else:
                topic_status = "Not attempted"

            topics_with_status.append({
                "topic_id": topic_id,
                "title": topic["title"],
                "topic_status": topic_status,
                "created_at": topic["created_at"]
            })

        return jsonify(topics_with_status), 200

    except Exception as e:
        logging.error(f"Error fetching user topics: {e}")
        return jsonify({"error": "Failed to fetch topics"}), 500