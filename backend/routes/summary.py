from flask import Blueprint, jsonify, request
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import logging

summary_bp = Blueprint('summary', __name__)
bp = summary_bp  # Alias for backward compatibility

# Initialize services
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)

@bp.route('/generate', methods=['POST'])
def generate_summary():
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        user_id = data.get('user_id')
        
        if not document_id or not user_id:
            return jsonify({"error": "Missing document_id or user_id"}), 400

        # Fetch document content
        response = supabase.table('documents').select('content').eq('id', document_id).eq('user_id', user_id).execute()
        if not response.data:
            return jsonify({"error": "Document not found"}), 404

        # Concatenate content
        content = "\n\n".join([chunk['content'] for chunk in response.data])
        
        # Generate summary
        prompt = f"""
        Create a comprehensive summary of the following document content.
        Focus on key points, main arguments, and important details.
        Use clear and concise language suitable for quick reference.
        
        Document Content:
        {content}
        """
        
        summary = llm.predict(prompt).strip()
        
        # Save summary to database
        supabase.table('summaries').insert({
            'document_id': document_id,
            'user_id': user_id,
            'content': summary
        }).execute()
        
        return jsonify({"summary": summary}), 200

    except Exception as e:
        logging.error(f"Summary generation error: {str(e)}")
        return jsonify({"error": "Failed to generate summary"}), 500

@bp.route('/document/<document_id>', methods=['GET'])
def get_document_summary(document_id):
    try:
        response = supabase.table('summaries').select('*').eq('document_id', document_id).execute()
        if response.data:
            return jsonify(response.data[0]), 200
        return jsonify({"error": "Summary not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500