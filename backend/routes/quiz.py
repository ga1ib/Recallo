from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
import logging
import os
import uuid
import hashlib
import json
from supabase import create_client
from process_pdf_for_quiz import process_pdf_for_quiz
from QA_ANSWER import generate_and_save_mcqs
from matching_q_a import evaluate_and_save_quiz

# Create blueprint
quiz_bp = Blueprint('quiz', __name__)

# Initialize configurations
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@quiz_bp.route('/quiz-question', methods=['POST'])
def quiz_question():
    """Upload file and process for quiz topic generation"""
    try:
        logging.info("Quiz-question endpoint called")
        user_id = request.form.get("user_id")
        file = request.files.get("file")

        logging.info(f"Received user_id: {user_id}")
        logging.info(f"Received file: {file.filename if file else 'None'}")

        if not user_id or not file:
            logging.error("Missing user_id or file")
            return jsonify({"error": "Missing user_id or file."}), 400

        # Read file bytes to compute hash
        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file.seek(0)  # Reset file pointer after reading

        if len(file_bytes) > 5 * 1024 * 1024:  # 5MB limit
            return jsonify({"error": "File is too large. Max size is 5MB."}), 413

        # Check if file hash already exists for this user
        try:
            response = supabase.table('topics') \
                .select('topic_id') \
                .eq('user_id', user_id) \
                .eq('hash_file', file_hash) \
                .execute()

            if response.data and len(response.data) > 0:
                logging.info(f"Duplicate upload detected for user {user_id} with file hash {file_hash}")
                return jsonify({"message": "You have already uploaded this file earlier."}), 409
        except Exception as e:
            logging.error(f"Error querying Supabase: {e}")
            return jsonify({"error": "Internal server error checking uploads."}), 500

        if allowed_file(file.filename):
            # Save file temporarily
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            temp_path = os.path.join(upload_folder, temp_filename)
            file.save(temp_path)

            # Process PDF for quiz topics
            result = process_pdf_for_quiz(temp_path, GEMINI_API_KEY, user_id, supabase, file_hash)

            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logging.info(f"🗑️ Deleted temporary file: {temp_path}")

            if result and result.get("status") == "success":
                return jsonify({"message": "Topics saved successfully."}), 200
            else:
                return jsonify({"error": "Failed to process PDF."}), 500

        return jsonify({"error": "Invalid file type."}), 400

    except Exception as e:
        logging.error(f"Error in quiz_question endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@quiz_bp.route("/generate-questions", methods=['POST', 'OPTIONS'])
def generate_questions():
    """Generate MCQ questions for a specific topic"""
    if request.method == 'OPTIONS':
        # Handle preflight CORS request
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 204

    data = request.get_json()
    topic_id = data.get("topic_id")
    difficulty = data.get("difficulty_mode", "hard")

    try:
        questions = generate_and_save_mcqs(topic_id, GEMINI_API_KEY, difficulty)

        # Prepare questions for frontend (strip sensitive data if needed)
        questions_for_frontend = [
            {   
                "question_id": q["question_id"],  
                "question_text": q["question_text"],
                "options": q["options"],
                "correct_answer": q.get("correct_answer"),
                "answer_text": q.get("answer_text"), 
                "explanation": q.get("explanation")
            }
            for q in questions
        ]

        response = jsonify({"questions": questions_for_frontend})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        return response, 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        return response, 500

@quiz_bp.route("/submit-answers", methods=["POST", "OPTIONS"])
@cross_origin()
def submit_answers():
    """Submit quiz answers and get evaluation"""
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        user_id = data.get("user_id")
        topic_id = data.get("topic_id")
        submitted_answers = data.get("submitted_answers")

        if not user_id or not topic_id or not submitted_answers:
            return jsonify({
                "error": "Missing one or more required fields: user_id, topic_id, submitted_answers"
            }), 400

        # Validate each answer object
        for ans in submitted_answers:
            if not isinstance(ans, dict):
                return jsonify({"error": "Invalid answer format. Each answer must be an object."}), 400
            if "question_id" not in ans or "selected_answer" not in ans:
                return jsonify({
                    "error": "Each answer must include 'question_id' and 'selected_answer'"
                }), 400

        result = evaluate_and_save_quiz(user_id, topic_id, submitted_answers)

        return jsonify({"message": "Quiz submitted successfully", "result": result}), 200

    except Exception as e:
        logging.exception("Error while processing submitted answers")
        return jsonify({"error": str(e)}), 500

@quiz_bp.route("/api/answer-analysis")
def get_answer_analysis():
    """Get detailed analysis of quiz answers for a specific attempt"""
    topic_id = request.args.get("topic_id")
    user_id = request.args.get("user_id")
    attempt_number = request.args.get("attempt_number")

    if not (topic_id and user_id and attempt_number):
        return jsonify({"error": "Missing required parameters"}), 400

    # Get all attempts for this user and topic
    attempts_resp = supabase.table("quiz_attempts") \
        .select("attempt_id, submitted_at, score") \
        .eq("topic_id", topic_id) \
        .eq("user_id", user_id) \
        .order("submitted_at") \
        .execute()
    attempts = attempts_resp.data

    if not attempts:
        return jsonify({"error": "No attempts found"}), 404

    try:
        attempt_idx = int(attempt_number) - 1
        selected_attempt = attempts[attempt_idx]
    except (IndexError, ValueError):
        return jsonify({"error": "Invalid attempt number"}), 400

    attempt_id = selected_attempt["attempt_id"]

    # Fetch answers for this attempt
    answers_resp = supabase.table("quiz_answers") \
        .select("question_id, selected_answer, selected_answer_text, is_correct") \
        .eq("attempt_id", attempt_id) \
        .execute()
    answers = answers_resp.data or []

    question_ids = [a["question_id"] for a in answers]
    if not question_ids:
        return jsonify({"error": "No answers found for this attempt"}), 404

    # Fetch questions info
    questions_resp = supabase.table("quiz_questions") \
        .select("question_id, prompt, answer, answer_option_text, explanation") \
        .in_("question_id", question_ids) \
        .execute()
    questions = questions_resp.data or []

    analysis = []

    for answer in answers:
        q = next((item for item in questions if item["question_id"] == answer["question_id"]), None)
        if not q:
            continue

        # Initialize defaults
        correct_option = q["answer"]
        selected_option = answer["selected_answer"]
        correct_option_text = ""
        selected_option_text = answer.get("selected_answer_text", "")
        options = {}

        try:
            if q["answer_option_text"]:
                options = json.loads(q["answer_option_text"])
                correct_option_text = options.get(correct_option, "")
                
                if not selected_option_text and selected_option:
                    selected_option_text = options.get(selected_option, "")

        except Exception as e:
            print(f"Error processing options for question {q['question_id']}: {str(e)}")

        analysis.append({
            "question_id": q["question_id"],
            "question_text": q["prompt"],
            "correct_option": correct_option,
            "correct_option_text": correct_option_text,
            "selected_option": selected_option,
            "selected_option_text": selected_option_text,
            "explanation": q.get("explanation", "No explanation provided"),
            "is_correct": answer["is_correct"],
            "all_options": options,
        })

    return jsonify({
        "questions": analysis,
        "attempt_data": {
            "score": selected_attempt.get("score"),
            "submitted_at": selected_attempt.get("submitted_at")
        }
    })

@quiz_bp.route("/api/progress/<user_id>", methods=["GET"])
def get_user_progress(user_id):
    """Get user progress across all quiz topics"""
    try:
        # Fetch all quiz attempts for the user
        response = supabase.table("quiz_attempts")\
            .select("topic_id, score, submitted_at")\
            .eq("user_id", user_id)\
            .order("submitted_at", desc=False)\
            .execute()

        if not response.data:
            return jsonify([]), 200

        attempts = response.data

        # Group attempts by topic_id
        topic_attempts_map = {}
        for attempt in attempts:
            topic_id = attempt["topic_id"]
            topic_attempts_map.setdefault(topic_id, []).append({
                "score": attempt["score"],
                "submitted_at": attempt["submitted_at"]
            })

        # Fetch topic metadata
        topic_ids = list(topic_attempts_map.keys())
        topics_response = supabase.table("topics")\
            .select("topic_id, title, file_name")\
            .in_("topic_id", topic_ids)\
            .execute()

        topic_meta_map = {t["topic_id"]: t for t in topics_response.data} if topics_response.data else {}

        # Prepare results
        results = []

        for topic_id, attempts_list in topic_attempts_map.items():
            # Sort by submitted_at ascending for proper chronological order
            sorted_attempts = sorted(attempts_list, key=lambda x: x["submitted_at"], reverse=False)

            latest_score = sorted_attempts[-1]["score"]  # Most recent attempt
            first_score = sorted_attempts[0]["score"]    # First attempt
            previous_score = sorted_attempts[-2]["score"] if len(sorted_attempts) > 1 else None

            # Calculate progress metrics
            progress_percent = None
            overall_progress_percent = None

            # Progress from previous attempt
            if previous_score is not None and previous_score != 0:
                progress_percent = round(((latest_score - previous_score) * 100.0 / previous_score), 2)

            # Overall progress from first attempt
            if len(sorted_attempts) > 1 and first_score != 0:
                overall_progress_percent = round(((latest_score - first_score) * 100.0 / first_score), 2)

            # Create history of all attempts
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