from flask import Blueprint, request, jsonify, current_app
import logging
import os
import hashlib
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from upload_pdf import process_pdf

# Create blueprint
documents_bp = Blueprint('documents', __name__)

# Initialize configurations
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)

# Global variable for recent file tracking
recent_file_uid = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route('/upload', methods=['POST'])
def upload_file():
    global recent_file_uid 
    
    logging.info("Upload route hit")
    user_id = request.form.get("user_id")
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Read file bytes to compute hash
    file_bytes = file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file.seek(0)  # Reset file pointer after reading

    # Check file size
    if file.content_length and file.content_length > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify({"error": "File is too large. Max size is 5MB"}), 413

    # Check if file hash already exists for this user
    try:
        response = supabase.table('documents') \
            .select('id') \
            .eq('user_id', user_id) \
            .eq('hash_file', file_hash) \
            .execute()
        
        if response.data and len(response.data) > 0:
            logging.info(f"Duplicate upload detected for user {user_id} with file hash {file_hash}")
            return jsonify({"message": "You have already uploaded this file earlier."}), 409
    except Exception as e:
        logging.error(f"Error querying Supabase: {e}")
        return jsonify({"error": "Internal server error checking uploads."}), 500

    # Process file upload
    if file and allowed_file(file.filename):
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        logging.info(f"📥 File saved: {file_path}")

        try:
            # Process PDF file
            success, chunk_count, uploaded_filename, file_uid = process_pdf(
                file_path, supabase, GEMINI_API_KEY, user_id, file_hash
            )

            recent_file_uid = file_uid  # Store in global variable
            logging.info(f"File UUID stored: {recent_file_uid}")

            if success:
                logging.info(f"📌 recent_filename set to: {uploaded_filename}")
                logging.info(f"🗂️ File UUID: {file_uid}")
                return jsonify({
                    "message": f"PDF processed. {chunk_count} chunks saved from '{uploaded_filename}'."
                }), 200
            else:
                return jsonify({"error": f"Failed to process PDF: {chunk_count}"}), 500

        except Exception as e:
            logging.error(f"Error during PDF processing: {str(e)}")
            return jsonify({"error": "Failed to process the PDF file."}), 500

    return jsonify({"error": "Invalid file type"}), 400

def get_summary():
    """Generate summary from uploaded document"""
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

        # Save summary to the first document row
        first_id = docs[0]['id']
        supabase.table("documents").update({"summary": summary}).eq("id", first_id).execute()

        return jsonify({"response": summary}), 200

    except Exception as e:
        logging.error(f"Error in get_summary: {e}")
        return jsonify({"error": "Failed to summarize"}), 500

def generate_questions():
    """Generate questions from uploaded document"""
    global recent_file_uid
    try:
        if not recent_file_uid:
            return jsonify({"error": "No recent file uploaded"}), 400

        docs = supabase.table('documents').select('content').eq('file_uuid', recent_file_uid).execute().data
        if not docs:
            return jsonify({"error": "No content found"}), 404

        concatenated_text = "\n\n".join(doc['content'] for doc in docs)

        prompt = f"""
        You are an expert educator with a deep understanding of how to generate relevant and insightful questions from a given text. Based on the following document, create a mixture of **Multiple Choice Questions (MCQs)** and **broad, open-ended questions** that focus on the most important topics discussed in the text.

        For each question:
        1. Provide the **correct answer** at the end of the question on a **separate line**.
        2. **Explain why** the answer is correct for **broad questions**, with a focus on the key concepts behind the question.
        3. Specify **which topic** the question is related to on a **separate line with a line gap**.
        4. Ensure the questions are well-structured, engaging, and relevant to the content.
        5. If applicable, provide at least **one resource or website** where users can learn more about each topic.
        6. **For MCQs**, do not provide explanations—just the question and the answer on separate lines.
        7. Options will be on a separate line with gaps between the 4 options as well as the question.
        8. Try to generate at least 5 questions.

        Here is the content you need to generate questions from:

        ======== PDF Content ========
        {concatenated_text}
        =============================

        Generated Questions and Answers:
        """
        
        questions = llm.predict(prompt)
        return jsonify({"response": questions.strip()}), 200
    except Exception as e:
        logging.error(f"Error in generate_questions: {e}")
        return jsonify({"error": "Failed to generate questions"}), 500