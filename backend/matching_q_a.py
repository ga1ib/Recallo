import uuid
import os 
import logging
import json
from dotenv import load_dotenv
from datetime import datetime
from supabase import create_client

# Initialize Supabase client (make sure these env variables are set)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_uuid():
    return str(uuid.uuid4())

def is_user_email_notification_enabled(user_id):
    """Check if user has email notifications enabled globally (default: True)"""
    try:
        resp = supabase.table("user_notification_settings") \
            .select("email_notifications_enabled") \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if resp.error or not resp.data:
            # Default to True if no settings found
            return True

        return resp.data.get("email_notifications_enabled", True)
    except Exception as e:
        logging.error(f"Error checking email notification settings: {e}")
        return True  # Default to enabled

def update_review_features(user_id, topic_id, topic_title, score):
    """Update or insert user_topic_review_features for scheduling system"""
    try:
        # Check if record exists (don't use .single() to avoid errors)
        existing_resp = supabase.table("user_topic_review_features") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("topic_id", topic_id) \
            .execute()

        current_time = datetime.now().isoformat()

        # Prepare data that matches the table structure
        data = {
            "user_id": user_id,
            "topic_id": topic_id,
            "title": topic_title,
            "quiz_score": int(score) if score == int(score) else float(score),
            "quiz_date": current_time,
            "last_attempt": current_time,
            "attempts_count": 1,
            "mastered": bool(score >= 8),
            "pass": 1 if score >= 8 else 0,  # Integer, not boolean
            "avg_score": float(score),
            "days_since_last_attempt": 0
        }

        if existing_resp.data and len(existing_resp.data) > 0:
            # Update existing record
            existing_record = existing_resp.data[0]
            # Increment attempts count
            data["attempts_count"] = int(existing_record.get("attempts_count", 0)) + 1
            # Update average score
            prev_avg = float(existing_record.get("avg_score", score))
            prev_count = int(existing_record.get("attempts_count", 0))
            data["avg_score"] = float(((prev_avg * prev_count) + score) / data["attempts_count"])
            # Update boolean/integer fields
            data["mastered"] = bool(score >= 8)
            data["pass"] = 1 if score >= 8 else 0  # Integer, not boolean

            supabase.table("user_topic_review_features") \
                .update(data) \
                .eq("user_id", user_id) \
                .eq("topic_id", topic_id) \
                .execute()
            logging.info(f"✅ Updated existing review features for user {user_id}, topic {topic_id}, score {score}")
        else:
            # Insert new record
            supabase.table("user_topic_review_features") \
                .insert(data) \
                .execute()
            logging.info(f"✅ Inserted new review features for user {user_id}, topic {topic_id}, score {score}")

    except Exception as e:
        logging.error(f"Error updating review features: {e}")
        import traceback
        traceback.print_exc()

def evaluate_and_save_quiz(user_id, topic_id, submitted_answers):
    import json

    # Extract question IDs
    question_ids = [ans["question_id"] for ans in submitted_answers]

    # Fetch correct answers and options
    correct_answers_res = supabase.table("quiz_questions") \
        .select("question_id, answer, answer_option_text") \
        .in_("question_id", question_ids) \
        .execute()

    if not correct_answers_res.data:
        raise Exception("Failed to fetch correct answers from Supabase")

    correct_answers_map = {}
    option_text_map = {}

    # Parse correct answers and answer text options
    for q in correct_answers_res.data:
        correct_answers_map[q["question_id"]] = q["answer"]

        try:
            option_text_map[q["question_id"]] = json.loads(q.get("answer_option_text", "{}"))
        except Exception as e:
            logging.warning(f"❌ Failed to parse answer_option_text for question {q['question_id']}: {e}")
            option_text_map[q["question_id"]] = {}

    # Compare answers and prepare for saving
    total_questions = len(submitted_answers)
    correct_count = 0
    answers_to_save = []

    for ans in submitted_answers:
        qid = ans["question_id"]
        selected = ans["selected_answer"]
        correct = correct_answers_map.get(qid)

        option_texts = option_text_map.get(qid, {})  # ✅ Make sure this is above both .get() calls

        correct_text = option_texts.get(correct, "N/A")
        selected_text = option_texts.get(selected, "N/A")

        is_correct = (selected == correct)

        if is_correct:
            correct_count += 1

        answers_to_save.append({
            "answer_id": generate_uuid(),
            "question_id": qid,
            "selected_answer": selected,
            "selected_answer_text": selected_text,
            "is_correct": is_correct
        })

    # Score calculation
    score = (correct_count / total_questions) * 10
    attempt_id = generate_uuid()

    # Save quiz attempt
    attempt_res = supabase.table("quiz_attempts").insert({
        "attempt_id": attempt_id,
        "user_id": user_id,
        "topic_id": topic_id,
        "score": score,
        "submitted_at": datetime.now().isoformat()
    }).execute()

    if not attempt_res.data:
        raise Exception("Failed to insert quiz attempt into Supabase")

    # Add attempt ID to each answer record
    for answer in answers_to_save:
        answer["attempt_id"] = attempt_id

    # Save all answers
    answers_res = supabase.table("quiz_answers").insert(answers_to_save).execute()
    if not answers_res.data:
        raise Exception("Failed to insert quiz answers into Supabase")

    # Update or insert progress
    progress_res = supabase.table("user_topic_progress") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("topic_id", topic_id) \
        .maybe_single() \
        .execute()

    progress_data = getattr(progress_res, 'data', None)

    if not progress_data:
        insert_progress_res = supabase.table("user_topic_progress").insert({
            "user_id": user_id,
            "topic_id": topic_id,
            "last_score": score,
            "attempts_count": 1,
            "mastered": score >= 7,
            "last_attempt": datetime.now().isoformat()
        }).execute()

        if not insert_progress_res or not insert_progress_res.data:
            raise Exception("Failed to insert user topic progress into Supabase")
    else:
        attempts_count = progress_data.get("attempts_count", 0) + 1
        mastered = progress_data.get("mastered", False) or (score >= 7)

        update_res = supabase.table("user_topic_progress").update({
            "last_score": score,
            "attempts_count": attempts_count,
            "mastered": mastered,
            "last_attempt": datetime.now().isoformat()
        }).eq("user_id", user_id).eq("topic_id", topic_id).execute()

        if not update_res or not update_res.data:
            raise Exception("Failed to update user topic progress in Supabase")

    # Update topic status
    new_status = "Completed" if score > 7 else "Weak"
    status_update = supabase.table("topics").update({
        "topic_status": new_status
    }).eq("topic_id", topic_id).execute()

    if not status_update or not status_update.data:
        logging.warning(f"⚠️ Failed to update topic_status to '{new_status}' for topic {topic_id}")

    # Send automatic email notification after quiz completion
    try:
        # Get user and topic information for email
        user_resp = supabase.table("users").select("email, name").eq("user_id", user_id).single().execute()
        topic_resp = supabase.table("topics").select("title").eq("topic_id", topic_id).single().execute()

        if user_resp.data and topic_resp.data:
            user_email = user_resp.data.get("email")
            user_name = user_resp.data.get("name", "Learner")
            topic_title = topic_resp.data.get("title", "Quiz Topic")

            # Check if user has email notifications enabled (default: True)
            notification_enabled = is_user_email_notification_enabled(user_id)

            if user_email and notification_enabled:
                from email_utils import send_exam_result_email
                email_sent = send_exam_result_email(user_email, user_name, topic_title, score)
                if email_sent:
                    logging.info(f"✅ Email sent successfully to {user_email} for quiz score {score}")
                else:
                    logging.error(f"❌ Failed to send email to {user_email}")
            else:
                logging.info(f"📧 Email notifications disabled for user {user_id}")

        # Update user_topic_review_features for scheduling system
        update_review_features(user_id, topic_id, topic_title, score)

    except Exception as e:
        logging.error(f"Error sending email notification: {e}")
        # Don't fail the quiz submission if email fails

    return {
        "score": score,
        "total_questions": total_questions,
        "correct_answers": correct_count
    }
		