import os
import hashlib
import re
from datetime import datetime
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain

def init_supabase():
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_llm():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)
    memory = ConversationBufferWindowMemory(k=10, return_messages=True)
    conversation = ConversationChain(llm=llm, memory=memory, verbose=True)
    embedding_fn = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
    return llm, memory, conversation, embedding_fn

def allowed_file(filename, allowed_extensions={'pdf', 'doc', 'docx', 'txt'}):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_time():
    return datetime.now().isoformat()

def log_error(message):
    print(f"[ERROR] {datetime.now()}: {message}")

def log_info(message):
    print(f"[INFO] {datetime.now()}: {message}")