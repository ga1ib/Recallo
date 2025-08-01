from flask import Blueprint, jsonify, request
import logging
from supabase import create_client
import os

progress_bp = Blueprint('progress', __name__, url_prefix='/api/progress')
bp = progress_bp  # Alias for backward compatibility

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@bp.route('/<user_id>', methods=['GET'])
def get_user_progress(user_id):
    try:
        response = supabase.table("quiz_attempts").select(
            "topic_id, score, submitted_at"
        ).eq("user_id", user_id).order("submitted_at", desc=False).execute()

        if not response.data:
            return jsonify([]), 200

        attempts = response.data
        topic_attempts_map = {}
        for attempt in attempts:
            topic_id = attempt["topic_id"]
            topic_attempts_map.setdefault(topic_id, []).append({
                "score": attempt["score"],
                "submitted_at": attempt["submitted_at"]
            })

        topic_ids = list(topic_attempts_map.keys())
        topics_response = supabase.table("topics").select(
            "topic_id, title, file_name"
        ).in_("topic_id", topic_ids).execute()
        topic_meta_map = {t["topic_id"]: t for t in topics_response.data} if topics_response.data else {}
        results = []

        for topic_id, attempts_list in topic_attempts_map.items():
            sorted_attempts = sorted(attempts_list, key=lambda x: x["submitted_at"], reverse=False)
            latest_score = sorted_attempts[-1]["score"]
            first_score = sorted_attempts[0]["score"]
            previous_score = sorted_attempts[-2]["score"] if len(sorted_attempts) > 1 else None

            progress_percent = None
            overall_progress_percent = None

            if previous_score is not None and previous_score != 0:
                progress_percent = round(((latest_score - previous_score) * 100.0 / previous_score), 2)

            if len(sorted_attempts) > 1 and first_score != 0:
                overall_progress_percent = round(((latest_score - first_score) * 100.0 / first_score), 2)

            attempt_history = []
            for i, attempt in enumerate(sorted_attempts):
                attempt_history.append({
                    "attempt_number": i + 1,
                    "score": attempt["score"],
                    "submitted_at": attempt["submitted_at"],
                    "improvement": None if i == 0 else round(attempt["score"] - sorted_attempts[i-1]["score"], 2)
                })

            meta = topic_meta_map.get(topic_id, {})
            results.append({
                "user_id": user_id,
                "topic_id": topic_id,
                "topic_title": meta.get("title", f"Topic {topic_id}"),
                "file_name": meta.get("file_name", "Unknown Document"),
                "latest_score": latest_score,
                "previous_score": previous_score,
                "first_score": first_score,
                "progress_percent": progress_percent,
                "overall_progress_percent": overall_progress_percent,
                "total_attempts": len(sorted_attempts),
                "attempt_history": attempt_history
            })

        return jsonify(results), 200

    except Exception as e:
        logging.error(f"Error fetching progress: {e}")
        return jsonify({"error": "Failed to fetch progress"}), 500