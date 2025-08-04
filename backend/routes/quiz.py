# Updated `quiz.py` without middleware integration

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

quiz_bp = Blueprint('quiz', __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@quiz_bp.route('/quiz-question', methods=['POST'])
def quiz_question():
    try:
        user_id = request.form.get("user_id")
        file = request.files.get("file")

        if not user_id or not file:
            return jsonify({"error": "Missing user_id or file."}), 400

        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file.seek(0)

        if len(file_bytes) > 5 * 1024 * 1024:
            return jsonify({"error": "File is too large. Max size is 5MB."}), 413

        try:
            response = supabase.table('topics').select('topic_id').eq('user_id', user_id).eq('hash_file', file_hash).execute()
            if response.data:
                return jsonify({"message": "You have already uploaded this file earlier."}), 409
        except Exception as e:
            return jsonify({"error": "Internal server error checking uploads."}), 500

        if allowed_file(file.filename):
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            temp_path = os.path.join(upload_folder, temp_filename)
            file.save(temp_path)

            result = process_pdf_for_quiz(temp_path, GEMINI_API_KEY, user_id, supabase, file_hash)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            if result and result.get("status") == "success":
                return jsonify({"message": "Topics saved successfully."}), 200
            else:
                return jsonify({"error": "Failed to process PDF."}), 500

        return jsonify({"error": "Invalid file type."}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@quiz_bp.route("/generate_questions", methods=['POST', 'OPTIONS'])
def generate_questions():
    if request.method == 'OPTIONS':
        # Respond to preflight CORS request
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 204

    data = request.get_json()
    print("the data is ", data)
    user_id = data.get("user_id")
    topic_id = data.get("topic_id")
    difficulty = data.get("difficulty_mode", "hard")

    try:
        questions = generate_and_save_mcqs(topic_id, GEMINI_API_KEY, difficulty,user_id)

        # Strip correct_answer for frontend
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
        traceback.print_exc()  # <-- logs to terminal
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        return response, 500

    

@quiz_bp.route("/submit-answers", methods=["POST", "OPTIONS"])
@cross_origin()
def submit_answers():
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
            return jsonify({"error": "Missing required fields."}), 400

        for ans in submitted_answers:
            if not isinstance(ans, dict) or "question_id" not in ans or "selected_answer" not in ans:
                return jsonify({"error": "Invalid answer format."}), 400

        result = evaluate_and_save_quiz(user_id, topic_id, submitted_answers)

        return jsonify({"message": "Quiz submitted successfully", "result": result}), 200

    except Exception as e:
        logging.exception("Error while processing submitted answers")
        return jsonify({"error": str(e)}), 500
