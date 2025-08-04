from flask import Blueprint, request, jsonify, random, HumanMessage
from flask_cors import CORS
from supabase import create_client
import os
import json
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Import ChatGoogleGenerativeAI from the correct library
from langchain_google_genai import ChatGoogleGenerativeAI

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

flashcards_bp = Blueprint('flashcards', __name__, url_prefix='/api/flashcards')
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)

# Initialize Supabase

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@flashcards_bp.route('/generate', methods=['POST'])
def generate_flashcards():
    try:
        data = request.get_json()
        attempt_id = data.get("attempt_id")
        user_id = data.get("user_id")
        topic_id = data.get("topic_id")
        print(f"Attempt ID: {attempt_id}, User ID: {user_id}")

        if not attempt_id or not user_id:
            return jsonify({"error": "Missing attempt_id or user_id"}), 400
        
        
        existing = supabase.from_("flashcards") \
            .select("core_concept, key_theory, common_mistake") \
            .eq("user_id", user_id) \
            .eq("attempt_id", attempt_id) \
            .execute()

        if existing.data and len(existing.data) == 10:
            return jsonify({
                "flashcards": existing.data,
                "message": "fetched",
            })
        
        
        # Step 1: Fetch quiz answers for this attempt
        answers_response = supabase.from_("quiz_answers").select(
            "question_id, selected_answer, is_correct"
        ).eq("attempt_id", attempt_id).execute()

        quiz_answers = answers_response.data or []
        
        if not quiz_answers:
            return jsonify({"error": "No answers found for this attempt"}), 404
        
        question_ids = [qa["question_id"] for qa in quiz_answers]
        
        # Step 2: Fetch corresponding questions
        questions_response = supabase.from_("quiz_questions").select(
            "question_id, prompt, answer, explanation, answer_option_text, concept_id"
        ).in_("question_id", question_ids).execute()

        question_map = {q["question_id"]: q for q in questions_response.data}
        
        # Fetch merged content from the topic
        topic_response = supabase.from_("topics").select("merged_content").eq("topic_id", topic_id).single().execute()
        merged_content = topic_response.data.get("merged_content") if topic_response.data else None

        
        merged = []
        for qa in quiz_answers:
            q = question_map.get(qa["question_id"])
            if q:
                merged.append({
                    "question_id": qa["question_id"],
                    "prompt": q["prompt"],
                    "options": q["answer_option_text"],
                    "correct_answer": q["answer"],
                    "selected_answer": qa["selected_answer"],
                    "is_correct": qa["is_correct"]
                })
                
        if not merged:
            return jsonify({"error": "No matching questions for answers"}), 404
                
        # --- Step 4: Sample 8 incorrect + (2 correct or more) ---
        incorrect = [item for item in merged if item["is_correct"] is False]
        correct = [item for item in merged if item["is_correct"] is True]

        random.shuffle(incorrect)
        random.shuffle(correct)

        incorrect_sample = incorrect[:min(8, len(incorrect))]
        remaining = 10 - len(incorrect_sample)
        correct_sample = correct[:min(remaining, len(correct))]

        flashcards_base = incorrect_sample + correct_sample
        random.shuffle(flashcards_base)
        
        
        # --- Step 5: Format examples for LLM prompt ---
        examples = [
            {
                "question": item["prompt"],
                "correct_answer": item["correct_answer"],
                "user_answer": item["selected_answer"],
                "is_wrong": item["is_correct"] is False
            }
            for item in flashcards_base
        ]

        prompt_examples = "\n".join(
            f"Q: {ex['question']}\nA: {ex['correct_answer']}\n"
            f"{'User Mistake: ' + (ex['user_answer'] or 'N/A') if ex['is_wrong'] else ''}"
            for ex in examples
        )



        # System prompt
        system_prompt = """You are a study assistant that generates concept flashcards from quiz questions.

            Each flashcard must contain:

            1. "core_concept" — the fundamental concept
            2. "key_theory" — a clear explanation of the concept
            3. "common_mistake" — (only if user got it wrong)

            🔁 You MUST return **exactly 10 items** as a JSON array.

            💡 Format:
            [
            {
                "core_concept": "...",
                "key_theory": "...",
                "common_mistake": "..." // only if relevant
            },
            ...
            ]

            ⛔️ Do not include any markdown, headings, or extra text.
            ⛔️ Do not repeat items. Stop after 10.
            ✅ Output should start with `[` and end with `]`.
            """



        # final_prompt = f"{system_prompt}\n\nQuiz Questions:\n{prompt_examples}"
        final_prompt = f"{system_prompt}\n\n📚 Topic Context:\n{merged_content or 'N/A'}\n\nQuiz Questions:\n{prompt_examples}"

        
        
        # --- Step 6: Log for debugging ---
        print("\n🧪 Sampled Flashcard Data:")
        for ex in examples:
            print(json.dumps(ex, indent=2))

        print("\n🧠 Final Prompt Sent to LLM:")
        print(final_prompt)

        # --- Step 7: LLM Call ---
        llm_response = llm.invoke([HumanMessage(content=final_prompt)])
        raw_text = llm_response.content

        try:
            flashcards = json.loads(raw_text)
        except json.JSONDecodeError:
            print("\n❌ LLM response parsing failed:")
            print(raw_text)
            return jsonify({
                "error": "Failed to parse flashcards",
                "llm_response": raw_text
            }), 500

        if (
            not isinstance(flashcards, list)
            or len(flashcards) != 10
            or not all("core_concept" in fc and "key_theory" in fc for fc in flashcards)
        ):
            raise ValueError("Flashcards must contain core_concept and key_theory, 10 items")

        print("\n✅ Final Flashcards:")
        print(json.dumps(flashcards, indent=2))

        # ✅ Step 4: Save flashcards
        now = datetime.now().isoformat()
        records = [{
            "user_id": user_id,
            "attempt_id": attempt_id,
            "topic_id": topic_id,
            "core_concept": fc["core_concept"],
            "key_theory": fc["key_theory"],
            "common_mistake": fc.get("common_mistake"),
            "created_at": now
        } for fc in flashcards]

        insert = supabase.from_("flashcards").insert(records).execute()
        if not insert.data:
            raise Exception("Failed to save flashcards to Supabase")

        return jsonify({"flashcards": flashcards,"message": "Generated"}), 200

    except Exception as e:
        logging.exception("Flashcard generation failed")
        return jsonify({"error": str(e)}), 500

    
