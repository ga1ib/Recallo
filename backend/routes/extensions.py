from flask import Blueprint, jsonify
import os
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain

# Create blueprint
extensions_bp = Blueprint('extensions', __name__)

# Initialize services
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)
memory = ConversationBufferWindowMemory(k=10, return_messages=True)
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)
embedding_fn = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)

@extensions_bp.route('/api/extensions/status', methods=['GET'])
def extensions_status():
    """Get status of AI extensions"""
    return jsonify({
        "llm": "initialized",
        "embeddings": "initialized",
        "memory": "initialized"
    })