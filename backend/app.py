from flask import Flask, Blueprint, request, jsonify, abort, session
from flask_cors import CORS, cross_origin
from flask import make_response
from flask_mail import Mail, Message
from datetime import datetime, timezone
from datetime import timedelta
from flask import current_app
from flask_mail import Message
import json
import os
import uuid
import logging
import hashlib
# import psycopg2  # Commented out - not used, app uses Supabase instead
import re
from datetime import datetime
from dotenv import load_dotenv
# from psycopg2.extras import RealDictCursor  # Commented out - not used
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.chains import RetrievalQA
from upload_pdf import process_pdf
# from upload_pdf import process_pdf  # Temporarily commented out due to Pinecone API key issue
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from config import PINECONE_API_KEY
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from fetch_text_supabase import fetch_text_from_supabase
from langchain.schema import HumanMessage
from process_pdf_for_quiz import process_pdf_for_quiz
from QA_ANSWER import generate_and_save_mcqs
from matching_q_a import evaluate_and_save_quiz


# === Load Environment Variables ===
load_dotenv()

# # ─── PostgreSQL Configuration ──────────────────────────────────────────────────
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = os.getenv("DB_PORT", "5432")
# DB_NAME = os.getenv("DB_NAME", "your_db")
# DB_USER = os.getenv("DB_USER", "your_user")
# DB_PASS = os.getenv("DB_PASS", "your_password")


conversation_bp = Blueprint("conversations", __name__)

# ─── Supabase & AI Configuration ───────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

# === Initialize Logging ===
logging.basicConfig(level=logging.DEBUG)

# === Initialize Flask App ===
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── Flask-Mail Configuration ─────────────────────
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME")

# ─── Mail Object Initialization ────────────────────
mail = Mail(app)

CORS(app, resources={
    r"/chat": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
    r"/upload": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
    r"/ask": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
    r"/quiz-question": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
    r"/generate-questions": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
    r"/submit-answers": {"origins": "http://localhost:5173", "methods": ["POST", "OPTIONS"]},
    r"/api/progress/.*": {"origins": "http://localhost:5173", "methods": ["GET", "OPTIONS"]},
    r"/api/answer-analysis": {"origins": "http://localhost:5173", "methods": ["GET", "OPTIONS"]},
    r"/*": {"origins": "*"}
    
}, supports_credentials=True)

# === Initialize Database Connections ===

# def get_db_connection():
#     return psycopg2.connect(
#         host=DB_HOST,
#         port=DB_PORT,
#         dbname=DB_NAME,
#         user=DB_USER,
#         password=DB_PASS,
#         cursor_factory=RealDictCursor
#     )


# === Initialize Supabase & Langchain Models ===
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)
memory = ConversationBufferWindowMemory(k=10, return_messages=True)
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)
embedding_fn = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)

# === Global Variable ===
recent_file_uid = None

# === Helper Functions ===
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_chat_log_supabase(user_message, response_message, message_id=None, user_id=None):
    """Insert chat log into Supabase (legacy function for backward compatibility)"""
    try:
        data = {
            "user_message": user_message,
            "response_message": response_message,
            "user_id": user_id,
            "message_id": message_id
        }
        response = supabase.table("chat_logs").insert(data).execute()
        logging.info("Inserted chat log into Supabase.")
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"Supabase insert error: {e}")
        return None

def insert_chat_log_supabase_with_conversation(user_id, conv_id, user_msg, resp_msg):
    """Insert chat log into Supabase with conversation tracking"""
    try:
        # Generate a unique message_id
        message_id = str(uuid.uuid4())

        data = {
            "user_id": user_id,
            "conversation_id": conv_id,
            "user_message": user_msg,
            "response_message": resp_msg,
            "message_id": message_id
        }

        response = supabase.table("chat_logs").insert(data).execute()

        # Update the conversation's updated_at timestamp
        update_response = supabase.table("conversations").update({
            "updated_at": "now()"
        }).eq("conversation_id", conv_id).execute()

        logging.info(f"Updated conversation timestamp for {conv_id}")

        logging.info(f"Inserted chat log into Supabase for conversation {conv_id}")
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"Supabase insert error: {e}")
        return None

def insert_chat_log_postgres(user_id, conv_id, user_msg, resp_msg):
    """Insert chat log into PostgreSQL (deprecated - keeping for compatibility)"""
    # This function is now deprecated since we're using Supabase
    # Redirect to Supabase function
    return insert_chat_log_supabase_with_conversation(user_id, conv_id, user_msg, resp_msg)
# ─── Conversations Endpoint ────────────────────────────────────────────────────
@app.route("/api/conversations", methods=["GET", "POST"])
def conversations():
    if request.method == "GET":
        # List all convos for a user
        user_id = request.args.get("user_id")
        if not user_id:
            abort(400, "Missing user_id")

        try:
            response = supabase.table("conversations").select("conversation_id, title, created_at, updated_at").eq("user_id", user_id).order("updated_at", desc=True).execute()
            return jsonify(response.data), 200
        except Exception as e:
            logging.error(f"Error fetching conversations: {e}")
            abort(500, "Failed to fetch conversations")

    elif request.method == "POST":
        # Create a brand‑new conversation
        data = request.get_json() or {}
        user_id = data.get("user_id")
        title = data.get("title", "New Chat")

        if not user_id:
            abort(400, "Missing user_id in body")

    # Generate unique conversation_id in Python
        new_conv_id = str(uuid.uuid4())

        try:
            response = supabase.table("conversations").insert({
                "conversation_id": new_conv_id,
                "user_id": user_id,
                "title": title
            }).execute()

            if response.data:
                return jsonify(response.data[0]), 201
            else:
                abort(500, "Failed to create conversation")
        except Exception as e:
            logging.error(f"Error creating conversation: {e}")
            abort(500, "Failed to create conversation")



# 🟦 Rename Conversation
@app.route("/api/conversations/<conversation_id>", methods=["PUT"])
def rename_conversation(conversation_id):
    data = request.get_json()
    new_title = data.get("title")

    if not new_title:
        return jsonify({"error": "Title is required"}), 400

    try:
        response = supabase.table("conversations").update({
            "title": new_title,
            "updated_at": "now()"  # Optional: to update timestamp
        }).eq("conversation_id", conversation_id).execute()

        return jsonify({"message": "Conversation renamed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# 🟥 Delete Conversation
@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    try:
        # Delete chat logs first (if FK constraint with cascade is not set)
        supabase.table("chat_logs").delete().eq("conversation_id", conversation_id).execute()

        # Then delete the conversation
        response = supabase.table("conversations").delete().eq("conversation_id", conversation_id).execute()

        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Chat Logs Endpoint ─────────────────────────────────────────────────────────
@app.route("/api/conversations/<conv_id>/logs", methods=["GET", "POST"])
def conversation_logs(conv_id):
    # Validate conv_id format
    try:
        uuid.UUID(conv_id)
    except ValueError:
        abort(400, "Invalid conversation_id")

    if request.method == "GET":
        # Fetch all logs for this conversation
        try:
            response = supabase.table("chat_logs").select("id, user_message, response_message, created_at").eq("conversation_id", conv_id).order("created_at", desc=False).execute()
            return jsonify(response.data), 200
        except Exception as e:
            logging.error(f"Error fetching conversation logs: {e}")
            abort(500, "Failed to fetch conversation logs")

    elif request.method == "POST":
       # Append a new chat log under this conversation
        payload = request.get_json() or {}
        user_id = payload.get("user_id")
        user_msg = payload.get("user_message")
        resp_msg = payload.get("response_message")

        if not all([user_id, user_msg, resp_msg]):
            abort(400, "Must include user_id, user_message, and response_message")

        new_log = insert_chat_log_supabase_with_conversation(user_id, conv_id, user_msg, resp_msg)
        if new_log:
            return jsonify(new_log), 201
        else:
            abort(500, "Failed to insert chat log")
# === Endpoints ===
@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get("message", "")
        user_id = request.json.get("user_id")
        conv_id = request.json.get("conversation_id")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        if not user_id:
            return jsonify({"error": "No user_id provided"}), 400

        logging.info(f"Received message: {user_message} from user: {user_id}")

        # Check if conversation_id is provided
        if conv_id:
            logging.info(f"Using existing conversation: {conv_id}")
            # Validate that the conversation exists and belongs to the user
            try:
                existing_conv = supabase.table("conversations").select("conversation_id").eq("conversation_id", conv_id).eq("user_id", user_id).execute()
                if not existing_conv.data:
                    logging.warning(f"Conversation {conv_id} not found for user {user_id}, creating new conversation")
                    conv_id = None  # Reset to create new conversation
                else:
                    logging.info(f"Validated existing conversation: {conv_id}")
            except Exception as e:
                logging.error(f"Error validating conversation: {e}")
                conv_id = None  # Reset to create new conversation

        # If no conversation_id is provided or validation failed, create a new conversation
        if not conv_id:
            logging.info("Creating new conversation")
            try:
                new_conv_response = supabase.table("conversations").insert({
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": "New Chat"
                }).execute()

                if new_conv_response.data:
                    conv_id = new_conv_response.data[0]["conversation_id"]
                    logging.info(f"Created new conversation: {conv_id}")
                else:
                    logging.error("Failed to create new conversation")
                    return jsonify({"error": "Failed to create conversation"}), 500
            except Exception as e:
                logging.error(f"Error creating conversation: {e}")
                return jsonify({"error": "Failed to create conversation"}), 500

        # Construct the enhanced, educational prompt
        prompt = f"""
        You are an AI assistant with a deep knowledge base designed to help users learn and understand any topic in the most effective and engaging way.

        Your role is to provide clear, accurate, and detailed explanations, making complex topics easy to understand.

        Respond to the user with a friendly, conversational tone, as if you're explaining the concept to a student. Break down the topic step by step when necessary, and give real-life examples to aid comprehension. Also, offer YouTube video suggestions that are relevant to the topic for further learning.

        Be empathetic, patient, and provide well-rounded answers. If the user asks for clarifications or examples, be ready to offer more detailed responses and give helpful suggestions.

        User message: {user_message}
        """

        # Use memory-based chain or your model to predict response
        reply = conversation.predict(input=user_message)

        # Save the conversation with proper tracking
        logging.info(f"Saving chat log for conversation: {conv_id}")
        saved_log = insert_chat_log_supabase_with_conversation(user_id, conv_id, user_message, reply)

        if not saved_log:
            logging.warning("Failed to save chat log, but continuing with response")

        # IMPORTANT: Return conversation_id so frontend can track it for subsequent messages
        return jsonify({
            "response": reply,
            "conversation_id": conv_id  # Frontend needs this to continue the same conversation
        }), 200

    except Exception as e:
        logging.error(f"/chat error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    global recent_file_uid 
    logging.info("Upload route hit")
    user_id = request.form.get("user_id")  # Get user ID from the form data
    print(f"User ID from upload: {user_id}")

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Read file bytes to compute hash
    file_bytes = file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file.seek(0)  # Reset file pointer after reading

    # Check file size (adjust if needed since content_length might not always be available)
    if file.content_length and file.content_length > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({"error": "File is too large. Max size is 5MB"}), 413

    # Check if file hash already exists for this user in Supabase
    try:
        response = supabase.table('documents') \
            .select('id') \
            .eq('user_id', user_id) \
            .eq('hash_file', file_hash) \
            .execute()
        
        if response.data and len(response.data) > 0:
            # File already uploaded by this user
            logging.info(f"Duplicate upload detected for user {user_id} with file hash {file_hash}")
            return jsonify({"message": "You have already uploaded this file earlier."}), 409
    except Exception as e:
        logging.error(f"Error querying Supabase: {e}")
        return jsonify({"error": "Internal server error checking uploads."}), 500

    # Validate file extension/type
    if file and allowed_file(file.filename):
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        logging.info(f"📥 File saved: {file_path}")

        try:
            # Process your PDF file as usual
            success, chunk_count, uploaded_filename, file_uid = process_pdf(file_path, supabase, GEMINI_API_KEY, user_id,file_hash)

            recent_file_uid = file_uid  # Store in global variable
            logging.info(f"File UUID stored: {recent_file_uid}")

            if success:
                logging.info(f"📌 recent_filename set to: {uploaded_filename}")
                logging.info(f"🗂️ File UUID: {file_uid}")
                return jsonify({"message": f"PDF processed. {chunk_count} chunks saved from '{uploaded_filename}'."}), 200
            else:
                return jsonify({"error": f"Failed to process PDF: {chunk_count}"}), 500

        except Exception as e:
            logging.error(f"Error during PDF processing: {str(e)}")
            return jsonify({"error": "Failed to process the PDF file."}), 500

    return jsonify({"error": "Invalid file type"}), 400
@app.route('/quiz-question', methods=['POST'])
def quiz_question():
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

        if len(file_bytes) > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({"error": "File is too large. Max size is 5MB."}), 413

        # Check if file hash already exists for this user in Supabase
        try:
            response = supabase.table('topics') \
                .select('topic_id') \
                .eq('user_id', user_id) \
                .eq('hash_file', file_hash) \
                .execute()

            if response.data and len(response.data) > 0:
                # File already uploaded by this user
                logging.info(f"Duplicate upload detected for user {user_id} with file hash {file_hash}")
                return jsonify({"message": "You have already uploaded this file earlier."}), 409
        except Exception as e:
            logging.error(f"Error querying Supabase: {e}")
            return jsonify({"error": "Internal server error checking uploads."}), 500

        if  allowed_file(file.filename):
            # Save file temporarily
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            temp_filename = f"{uuid.uuid4()}_{file.filename}"
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            file.save(temp_path)

            # Process PDF for quiz topics and save them to Supabase
            result = process_pdf_for_quiz(temp_path, GEMINI_API_KEY, user_id, supabase,file_hash)

            # Clean up
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

# exam route
@app.route("/generate-questions", methods=['POST', 'OPTIONS'])
def generate_questions():
    if request.method == 'OPTIONS':
        # Respond to preflight CORS request
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

@app.route("/submit-answers", methods=["POST", "OPTIONS"])
@cross_origin()  # Add this decorator
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
            return jsonify({"error": "Missing one or more required fields: user_id, topic_id, submitted_answers"}), 400

        # Validate each answer object has a 'question_id' and 'selected_answer'
        for ans in submitted_answers:
            if not isinstance(ans, dict):
                return jsonify({"error": "Invalid answer format. Each answer must be an object."}), 400
            if "question_id" not in ans or "selected_answer" not in ans:
                return jsonify({"error": "Each answer must include 'question_id' and 'selected_answer'"}), 400

        result = evaluate_and_save_quiz(user_id, topic_id, submitted_answers)

        return jsonify({"message": "Quiz submitted successfully", "result": result}), 200

    except Exception as e:
        logging.exception("Error while processing submitted answers")
        return jsonify({"error": str(e)}), 500

@app.route("/api/answer-analysis")
def get_answer_analysis():
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

    # Fetch answers for this attempt (including selected_answer_text)
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
                # Get correct option text from the JSON
                correct_option_text = options.get(correct_option, "")
                
                # If selected_answer_text wasn't stored, get it from options
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
        "attempt_data": {  # Add attempt metadata
            "score": selected_attempt.get("score"),
            "submitted_at": selected_attempt.get("submitted_at")
        }
    })

# Helper to convert 'A', 'B' etc. to option text
def option_letter_to_text(letter, answer_option_text):
    if not letter or not answer_option_text:
        return ""

    options = {}
    for line in answer_option_text.strip().splitlines():
        if "." in line:
            parts = line.strip().split(".", 1)
            if len(parts) == 2:
                key = parts[0].strip().upper()
                val = parts[1].strip()
                options[key] = val

    return options.get(letter.upper(), "")


@app.route("/api/progress/<user_id>", methods=["GET"])
def get_user_progress(user_id):
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
            # Sort by submitted_at ascending (oldest first) for proper chronological order
            sorted_attempts = sorted(attempts_list, key=lambda x: x["submitted_at"], reverse=False)

            latest_score = sorted_attempts[-1]["score"]  # Last (most recent) attempt
            first_score = sorted_attempts[0]["score"]    # First attempt
            previous_score = sorted_attempts[-2]["score"] if len(sorted_attempts) > 1 else None

            # Calculate different types of progress
            progress_percent = None
            overall_progress_percent = None

            # Progress from previous attempt
            if previous_score is not None and previous_score != 0:
                progress_percent = round(((latest_score - previous_score) * 100.0 / previous_score), 2)

            # Overall progress from first attempt
            if len(sorted_attempts) > 1 and first_score != 0:
                overall_progress_percent = round(((latest_score - first_score) * 100.0 / first_score), 2)

            # Create history of all attempts for frontend
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
                "progress_percent": progress_percent,  # Progress from previous attempt
                "overall_progress_percent": overall_progress_percent,  # Progress from first attempt
                "total_attempts": len(sorted_attempts),
                "attempt_history": attempt_history
            })

        return jsonify(results), 200

    except Exception as e:
        logging.error(f"Error fetching progress: {e}")
        return jsonify({"error": "Failed to fetch progress"}), 500



@app.route('/ask', methods=['POST'])
def ask():
    try:
        user_message = request.json.get("message", "")  # Get the user's message
        user_id = request.json.get("user_id")
        
        # List of phrases that indicate the user wants a summary or overview
        summary_keywords = [
            "summarize", "overview", "summary", "what is on this file", "what is this file about", 
            "can you summarize", "give me a summary", "summarize the document", "overview of this file",
            "tell me about this file", "what's in this document", "can you give me the content of this file",
            "give me an overview", "give me the summary","summary of this file", "summarize this file", "summarize this document",
            "give me a summary of this file", "give me a summary of this document","summarise"
        ]
        
        # Expanded list of phrases indicating the user wants to generate questions
        question_keywords = [
            "generate questions","generate question", "make questions","make question", "create questions","create question", "ask questions", 
            "can you make questions for this document", "can you generate questions from this", 
            "create quiz questions", "generate quiz questions", "formulate questions from this", 
            "please make some questions", "please generate questions", "can you suggest questions", 
            "ask about this document", "can you create some questions", "create some questions for me", 
            "formulate questions", "suggest questions based on this", "can you create a quiz", 
            "can you ask some questions", "make some questions about this","create some questions","give me some questions",
            "generate questions from this file", "generate questions from this document", "make questions from this file",
            "make questions from this document", "create questions from this file", "create questions from this document",
            "ask questions about this file", "ask questions about this document", "can you generate questions from this file",
            "can you generate questions from this document", "can you make questions from this file", "can you make questions from this document",
        ]

        # If the user asks for a summary, trigger the summary function
        # if any(re.search(r'\b' + re.escape(keyword) + r'\b', user_message, re.IGNORECASE) for keyword in summary_keywords):
        #     return get_summary()

        # # If the user asks to generate questions, trigger question generation
        # elif any(re.search(r'\b' + re.escape(keyword) + r'\b', user_message, re.IGNORECASE) for keyword in question_keywords):
        #     return generate_questions()

        # For any other question, perform similarity search and provide an answer
        return get_answer_from_file(user_message, user_id)

    except Exception as e:
        logging.error(f"❌ Ask route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500



# === Functional Chains ===
def get_summary():
    try:
        global recent_file_uid

        if not recent_file_uid:
            return jsonify({"error": "No recent file uploaded"}), 400

        response = supabase.table('documents').select('id', 'content').eq('file_uuid', recent_file_uid).execute()
        docs = response.data

        if not docs:
            return jsonify({"error": "No content found for the given file."}), 404

        concatenated_text = "\n\n".join(doc['content'] for doc in docs)

        prompt = f"""
        You are an expert assistant with a deep understanding of how to summarize complex documents in a clear, concise, and professional manner. Based on the following content, summarize the key points in a way that is easy to understand, highlighting the most important information while keeping the summary brief and to the point.

        Please focus on:
        1. Extracting the core ideas and themes.
        2. Presenting the summary in a structured format with key takeaways.
        3. Avoiding unnecessary details or long explanations.

        Make sure the summary is **short and professional**, providing only the most relevant and actionable insights.

        Here is the content you need to summarize:

        ======== PDF Content ========
        {concatenated_text}
        =============================

        Your summary:
        """

        summary = llm.predict(prompt)
        summary = summary.strip()

        # Save summary to the first document row associated with this file
        first_id = docs[0]['id']
        supabase.table("documents").update({"summary": summary}).eq("id", first_id).execute()

        # Optional: log the interaction
        insert_chat_log_supabase("Summarize Request", summary)

        return jsonify({"response": summary}), 200

    except Exception as e:
        logging.error(f"Error in get_summary: {e}")
        return jsonify({"error": "Failed to summarize"}), 500

def generate_questions():
    global recent_file_uid
    try:
        if not recent_file_uid:
            return jsonify({"error": "No recent file uploaded"}), 400

        docs = supabase.table('documents').select('content').eq('file_uuid', recent_file_uid).execute().data
        if not docs:
            return jsonify({"error": "No content found"}), 404

        concatenated_text = "\n\n".join(doc['content'] for doc in docs)

        prompt = f"""
        You are an expert at generating questions from a given text. Based on the following document, create relevant and insightful questions that can be asked:You are an expert educator with a deep understanding of how to generate relevant and insightful questions from a given text. Based on the following document, create a mixture of **Multiple Choice Questions (MCQs)** and **broad, open-ended questions** that focus on the most important topics discussed in the text. These questions should reflect the depth and complexity of the material, similar to what a professional-grade teacher would ask.

        For each question:

        1. Provide the **correct answer** at the end of the question on a **separate line**.
        2. **Explain why** the answer is correct for **broad questions**, with a focus on the key concepts behind the question. Keep the explanation concise, just a few sentences.
        3. Specify **which topic** the question is related to on a **separate line with a line gap** (e.g., "Topic: [Topic Name]").
        4. Ensure the questions are well-structured, engaging, and relevant to the content.
        5. If applicable, provide at least **one resource or website** where users can learn more about each topic (this is **optional** and should be on a **separate new line with a line gap** if included).
        6. **For MCQs**, do not provide explanations—just the question and the answer on separate lines.
        7. **For broad questions**, make sure the explanation is concise, focusing on key ideas.
        8. Options will be on a separate line and make gap between the 4 options as well as the question so that it is easy to read.
        9. It is not mandatory to generate 10 questions, but try to generate at least 5 questions.

        Here is the content you need to generate questions from:

        ======== PDF Content ========
        {concatenated_text}
        =============================

        Generated Questions and Answers will be in the following format:

        1. **Question**: [Insert Question Here]

        **Answer**: [Insert Correct Answer Here]

        **Topic**: [Insert Topic Name Here]

        [Optional: **Learn More**: [Insert Learning Resource or Website Here]]

        2. **Question**: [Insert Question Here]

        **Answer**: [Insert Correct Answer Here]

        **Explanation**: [Provide Explanation for the Answer in a Few Sentences]

        **Topic**: [Insert Topic Name Here]

        [Optional: **Learn More**: [Insert Learning Resource or Website Here]]

        [Repeat as needed for additional questions]
        """
        questions = llm.predict(prompt)
        insert_chat_log_supabase("Generate Questions Request", questions.strip())
        return jsonify({"response": questions.strip()}), 200
    except Exception as e:
        logging.error(f"Error in generate_questions: {e}")
        return jsonify({"error": "Failed to generate questions"}), 500

def get_answer_from_file(user_query, user_id):
    try:
        # # Get input from the request body
        # user_query = request.json.get("user_query")
        # user_id = request.json.get("user_id")
        userID=user_id;
        userQuery= user_query;
        print("get_answer_from_file called with user_query:", user_query, "and user_id:", user_id)

        if not user_query or not user_id:
            return jsonify({"error": "Missing user_query or user_id"}), 400


        # Initialize Pinecone client
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        # Get existing index
        index = pc.Index("document-index")

        # Set up Langchain Pinecone VectorStore
        vectorstore = PineconeVectorStore(
            index=index,
            embedding=embedding_fn
        )

        query_embedding = embedding_fn.embed_query(userQuery)

        pinecone_results = index.query(
            vector=query_embedding,
            filter={"user_id": userID},
            top_k=5,
            include_metadata=True
        )

        print(f"Pinecone Matches: {pinecone_results['matches']}")
        # Check if no matches found
        if not pinecone_results['matches']:
            return jsonify({"response": "No relevant content found."}), 200


        relevant_docs = []
        for match in pinecone_results['matches']:
            chunk_id = match['id']
            chunk_data = fetch_text_from_supabase(supabase, chunk_id, user_id)

        if chunk_data:
            relevant_docs.append(chunk_data)
            print(f"Chunk Text: {chunk_data}")


        if relevant_docs:
            # Concatenate or process relevant_docs as needed before LLM
            combined_text = "\n".join(relevant_docs)
            # Build chat message properly
            prompt = combined_text + "\n\nUser Question: " + user_query
            result = llm([HumanMessage(content=prompt)])

            return jsonify({
                "response": result.content,
                "source_documents": relevant_docs
            }), 200
        else:
            return jsonify({"response": "No relevant content found."}), 200

    except Exception as e:
        logging.error(f"Error in get_answer_from_file: {e}")
        return jsonify({"error": "Failed to fetch answer"}), 500


def get_explanation_from_api(user_query):
    try:
        reply = llm.predict(user_query)
        return jsonify({"response": reply.strip()}), 200
    except Exception as e:
        logging.error(f"Error in get_explanation_from_api: {e}")
        return jsonify({"error": "Fallback failed"}), 500

    # ─── Helpers ──────────────────────────────────────────────────────────────────

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

# Assume user_id, topic_id, and score are already defined

@app.route("/send-exam-email", methods=["POST"])
def send_exam_email():
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
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Mail send failed: {e}")
        return False

def record_notification(user_id, topic_id, notif_type, message):
    """Log the sent notification."""
    now = datetime.now(timezone.utc)  # ✅ updated line
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
# ─── Core Processor ───────────────────────────────────────────────────────────
def process_notifications():
    """
    Fetch each user/topic from user_topic_review_features
    and send daily or weekly reminders according to score & preferences.
    """
    # 1. Grab all topic review features
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

        # 2. Check if user has global email notifications enabled
        if not is_user_email_notification_enabled_global(uid):
            continue

        # 3. Check if user has daily reminders enabled (for scores < 8)
        if score < 8 and not is_daily_reminders_enabled(uid):
            continue

        # 4. Skip if user turned off notifications for this specific topic
        if not is_topic_notification_enabled(uid, tid):
            continue

        # 5. Determine notification type
        if score < 8:
            nt = "daily"
        else:
            nt = "weekly"

        # 6. Avoid duplicates
        if has_been_notified_today(uid, tid, nt):
            continue

        # 7. Lookup user email and name
        try:
            user_resp = supabase.table("users").select("email, name").eq("user_id", uid).single().execute()
            if not user_resp.data:
                logging.error(f"Could not find user email for {uid}")
                continue
        except Exception as e:
            logging.error(f"Error fetching user {uid}: {e}")
            continue

        # 8. Send & record
        user_email = user_resp.data["email"]
        user_name = user_resp.data.get("name", "Learner")

        from email_utils import send_reminder_email
        if send_reminder_email(user_email, user_name, title, score, nt):
            message_body = f"{nt.title()} reminder sent for {title} (score: {score}/10)"
            record_notification(uid, tid, nt, message_body)
            logging.info(f"✅ Sent {nt} reminder to {user_email} for topic: {title}")
        else:
            logging.error(f"❌ Failed to send {nt} reminder to {user_email}")
# ─── Optional Trigger Route ────────────────────────────────────────────────────
@app.route("/api/run-notifications", methods=["POST"])
def run_notifications_route():
    # (Protect this route in prod with an API key or auth check!)
    process_notifications()
    return jsonify({"message": "Notifications processed"}), 200

# ─── Topics Endpoint ───────────────────────────────────────────────────────────
@app.route("/api/topics/<user_id>", methods=["GET"])
def get_user_topics(user_id):
    """Get all topics for a specific user"""
    try:
        # Fetch topics for the user
        topics_resp = supabase.table("topics") \
            .select("topic_id, title, created_at") \
            .eq("user_id", user_id) \
            .execute()

        if not topics_resp.data:
            return jsonify([]), 200

        # Get quiz attempts to determine topic status
        topics_with_status = []
        for topic in topics_resp.data:
            topic_id = topic["topic_id"]

            # Get latest quiz attempt for this topic
            attempt_resp = supabase.table("quiz_attempts") \
                .select("score") \
                .eq("user_id", user_id) \
                .eq("topic_id", topic_id) \
                .order("submitted_at", desc=True) \
                .limit(1) \
                .execute()

            # Determine status based on latest score
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

# ─── User Notification Settings Endpoints ─────────────────────────────────────
@app.route("/api/notification-settings/<user_id>", methods=["GET"])
def get_notification_settings(user_id):
    """Get user's notification preferences"""
    try:
        # Default settings (used when tables don't exist or no records found)
        global_settings = {
            "email_notifications_enabled": True,
            "daily_reminders_enabled": True
        }
        topic_settings = {}

        # Try to get global email notification setting
        try:
            global_resp = supabase.table("user_notification_settings") \
                .select("email_notifications_enabled, daily_reminders_enabled") \
                .eq("user_id", user_id) \
                .execute()

            if global_resp.data and len(global_resp.data) > 0:
                global_settings.update(global_resp.data[0])
        except Exception as e:
            logging.info(f"No global notification settings found for user {user_id}: {e}")

        # Try to get topic-specific notification preferences
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
        # Return default settings instead of error
        return jsonify({
            "global_settings": {
                "email_notifications_enabled": True,
                "daily_reminders_enabled": True
            },
            "topic_settings": {}
        }), 200

@app.route("/api/notification-settings/<user_id>", methods=["PUT"])
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
                # Check if record exists
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
                    # Update existing
                    supabase.table("user_notification_settings") \
                        .update(settings_data) \
                        .eq("user_id", user_id) \
                        .execute()
                else:
                    # Insert new
                    supabase.table("user_notification_settings") \
                        .insert(settings_data) \
                        .execute()
            except Exception as e:
                logging.error(f"Error updating global settings: {e}")
                # Continue with topic settings even if global settings fail

        # Update topic-specific settings
        for topic_id, enabled in topic_settings.items():
            try:
                # Check if record exists
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
                    # Update existing
                    supabase.table("user_topic_notification_preferences") \
                        .update(topic_data) \
                        .eq("user_id", user_id) \
                        .eq("topic_id", topic_id) \
                        .execute()
                else:
                    # Insert new
                    supabase.table("user_topic_notification_preferences") \
                        .insert(topic_data) \
                        .execute()
            except Exception as e:
                logging.error(f"Error updating topic setting for {topic_id}: {e}")
                # Continue with next topic

        return jsonify({"message": "Notification settings updated successfully"}), 200

    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return jsonify({"error": "Failed to update notification settings"}), 500

# === Run App ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)