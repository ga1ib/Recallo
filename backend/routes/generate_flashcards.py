# routes/flashcards.py

import os
import json
import logging
from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI

generate_flashcards_bp = Blueprint("generate_flashcards", __name__)

# Environment fallback (used for early initialization)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Supabase immediately
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Don't initialize LLM at import time to avoid hanging
llm = None

def get_llm():
    """Initialize LLM on demand"""
    global llm
    if llm is None and GEMINI_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=GEMINI_API_KEY,
                temperature=0.7
            )
            logging.info("✅ Gemini LLM initialized successfully")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Gemini LLM: {e}")
            llm = None
    return llm

@generate_flashcards_bp.route("/api/generate_flashcards", methods=["POST", "OPTIONS"])
def generate_flashcards():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 204

    try:
        # Initialize LLM on demand
        current_llm = get_llm()
        if not current_llm:
            response = jsonify({"error": "Gemini API not configured or failed to initialize"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 500

        data = request.get_json()
        if not data:
            response = jsonify({"error": "No JSON data provided"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 400

        attempt_id = data.get("attempt_id")
        user_id = data.get("user_id")

        # Detailed validation with better error messages
        if not attempt_id:
            response = jsonify({"error": "Missing attempt_id", "received_data": data})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 400

        if not user_id:
            response = jsonify({"error": "Missing user_id", "received_data": data})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 400

        # Log the received data for debugging
        logging.info(f"Received flashcard request: attempt_id={attempt_id}, user_id={user_id}")

        try:
            response = supabase.rpc("get_quiz_questions_with_answers", {
                "p_attempt_id": attempt_id,
                "p_user_id": user_id
            }).execute()
        except Exception as exc:
            error_response = jsonify({"error": f"Supabase RPC failed: {str(exc)}"})
            error_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            error_response.headers.add("Access-Control-Allow-Credentials", "true")
            return error_response, 500

        if not response.data:
            error_response = jsonify({
                "error": "No quiz data found",
                "details": f"No quiz questions found for attempt_id: {attempt_id} and user_id: {user_id}",
                "suggestion": "Make sure the user has completed a quiz for this topic"
            })
            error_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            error_response.headers.add("Access-Control-Allow-Credentials", "true")
            return error_response, 404

        all_data = response.data
        incorrect = [q for q in all_data if q.get("is_correct") is False]
        correct = [q for q in all_data if q.get("is_correct") is True]

        incorrect_sample = incorrect[:min(8, len(incorrect))]
        remaining = 10 - len(incorrect_sample)
        correct_sample = correct[:remaining]

        examples = [
            {
                "question": q.get("prompt"),
                "correct_answer": q.get("answer"),
                "user_answer": q.get("selected_answer"),
                "is_wrong": not q.get("is_correct")
            }
            for q in incorrect_sample + correct_sample
        ]

        # Generate prompt for Gemini
        system_prompt = """You are a study assistant that generates concept flashcards from quiz questions.
Each flashcard should have:
1. 'core_concept' - The fundamental concept being tested
2. 'key_theory' - The underlying theory or principle
3. 'common_mistake' - (Only if user got it wrong) Why the mistake happens

Return exactly 10 flashcards in JSON like this:
[{
  "core_concept": "...",
  "key_theory": "...",
  "common_mistake": "..." // only if relevant
}, ...]"""

        quiz_examples = "\n".join(
            f"Q: {ex['question']}\nA: {ex['correct_answer']}\n"
            f"{'User Mistake: ' + ex['user_answer'] if ex['is_wrong'] else ''}\n"
            for ex in examples
        )

        final_prompt = f"{system_prompt}\n\nQuiz Questions:\n{quiz_examples}"

        # Initialize variables for error handling
        raw_output = ""
        cleaned_output = ""

        try:
            logging.info("🤖 Calling Gemini LLM...")
            llm_response = current_llm.invoke([{"role": "user", "content": final_prompt}])
            raw_output = llm_response.content
            logging.info(f"📝 LLM raw output: {raw_output[:200]}...")

            # Clean the output - remove markdown code blocks if present
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]  # Remove ```json
            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:]   # Remove ```
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]  # Remove trailing ```
            cleaned_output = cleaned_output.strip()

            logging.info(f"🧹 Cleaned output: {cleaned_output[:200]}...")
            flashcards = json.loads(cleaned_output)
            logging.info(f"✅ Parsed {len(flashcards)} flashcards")

            if not isinstance(flashcards, list) or len(flashcards) != 10:
                raise ValueError(f"Invalid or incomplete flashcard output: expected 10 flashcards, got {len(flashcards) if isinstance(flashcards, list) else 'non-list'}")

            save_flashcards_to_db(user_id, attempt_id, flashcards)
            success_response = jsonify({"flashcards": flashcards})
            success_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            success_response.headers.add("Access-Control-Allow-Credentials", "true")
            return success_response

        except json.JSONDecodeError as e:
            logging.error(f"❌ JSON decode error: {e}")
            logging.error(f"Raw output: {raw_output}")
            logging.error(f"Cleaned output: {cleaned_output}")
            error_response = jsonify({"error": "Failed to parse Gemini output", "raw": raw_output[:500], "cleaned": cleaned_output[:500], "json_error": str(e)})
            error_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            error_response.headers.add("Access-Control-Allow-Credentials", "true")
            return error_response, 500
        except Exception as e:
            logging.error(f"❌ LLM processing error: {e}")
            import traceback
            traceback.print_exc()
            error_response = jsonify({"error": f"LLM processing failed: {str(e)}"})
            error_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
            error_response.headers.add("Access-Control-Allow-Credentials", "true")
            return error_response, 500

    except Exception as e:
        logging.exception("Unexpected failure in flashcard generation")
        error_response = jsonify({"error": str(e)})
        error_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        error_response.headers.add("Access-Control-Allow-Credentials", "true")
        return error_response, 500

def save_flashcards_to_db(user_id, attempt_id, flashcards):
    """Save flashcards to database - placeholder implementation"""
    # TODO: Implement actual Supabase `insert` call to store flashcards if needed
    logging.info(f"Would save {len(flashcards)} flashcards for user {user_id}, attempt {attempt_id}")
    pass
