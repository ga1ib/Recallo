from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging
import uuid
import os
from supabase import create_client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from fetch_text_supabase import fetch_text_from_supabase

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize Supabase & AI components
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)
memory = ConversationBufferWindowMemory(k=10, return_messages=True)
conversation = ConversationChain(llm=llm, memory=memory, verbose=True)
embedding_fn = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)

def insert_chat_log_supabase_with_conversation(user_id, conv_id, user_msg, resp_msg):
    """Insert chat log into Supabase with conversation tracking"""
    try:
        message_id = str(uuid.uuid4())
        data = {
            "user_id": user_id,
            "conversation_id": conv_id,
            "user_message": user_msg,
            "response_message": resp_msg,
            "message_id": message_id
        }
        
        response = supabase.table("chat_logs").insert(data).execute()
        
        # Update conversation timestamp
        supabase.table("conversations").update({
            "updated_at": "now()"
        }).eq("conversation_id", conv_id).execute()
        
        logging.info(f"Inserted chat log into Supabase for conversation {conv_id}")
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"Supabase insert error: {e}")
        return None

@chat_bp.route('/chat', methods=['POST', 'OPTIONS'])
@cross_origin()
def chat():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    try:
        if not request.json:
            logging.error("No JSON data received in chat request")
            return jsonify({"error": "No JSON data provided"}), 400

        user_message = request.json.get("message", "")
        user_id = request.json.get("user_id")
        conv_id = request.json.get("conversation_id")

        logging.info(f"Chat request - user_id: {user_id}, message: {user_message[:50]}...")

        if not user_message:
            logging.error("No message provided in chat request")
            return jsonify({"error": "No message provided"}), 400
        if not user_id:
            logging.error("No user_id provided in chat request")
            return jsonify({"error": "No user_id provided"}), 400

        logging.info(f"Received message: {user_message} from user: {user_id}")

        # Validate existing conversation
        if conv_id:
            try:
                existing_conv = supabase.table("conversations").select("conversation_id").eq("conversation_id", conv_id).eq("user_id", user_id).execute()
                if not existing_conv.data:
                    conv_id = None
            except Exception as e:
                logging.error(f"Error validating conversation: {e}")
                conv_id = None

        # Create new conversation if needed
        if not conv_id:
            try:
                new_conv_response = supabase.table("conversations").insert({
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": "New Chat"
                }).execute()

                if new_conv_response.data:
                    conv_id = new_conv_response.data[0]["conversation_id"]
                else:
                    return jsonify({"error": "Failed to create conversation"}), 500
            except Exception as e:
                logging.error(f"Error creating conversation: {e}")
                return jsonify({"error": "Failed to create conversation"}), 500

        # Generate response
        prompt = f"""
        You are an AI assistant with a deep knowledge base designed to help users learn and understand any topic in the most effective and engaging way.

        Your role is to provide clear, accurate, and detailed explanations, making complex topics easy to understand.

        Respond to the user with a friendly, conversational tone, as if you're explaining the concept to a student. Break down the topic step by step when necessary, and give real-life examples to aid comprehension. Also, offer YouTube video suggestions that are relevant to the topic for further learning.

        Be empathetic, patient, and provide well-rounded answers. If the user asks for clarifications or examples, be ready to offer more detailed responses and give helpful suggestions.

        User message: {user_message}
        """

        reply = conversation.predict(input=user_message)

        # Save conversation
        saved_log = insert_chat_log_supabase_with_conversation(user_id, conv_id, user_message, reply)
        if not saved_log:
            logging.warning("Failed to save chat log, but continuing with response")

        return jsonify({
            "response": reply,
            "conversation_id": conv_id
        }), 200

    except Exception as e:
        logging.error(f"/chat error: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@chat_bp.route('/ask', methods=['POST'])
def ask():
    try:
        user_message = request.json.get("message", "")
        user_id = request.json.get("user_id")
        
        return get_answer_from_file(user_message, user_id)

    except Exception as e:
        logging.error(f"❌ Ask route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def get_answer_from_file(user_query, user_id):
    try:
        if not user_query or not user_id:
            return jsonify({"error": "Missing user_query or user_id"}), 400

        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("document-index")
        
        # Perform similarity search
        query_embedding = embedding_fn.embed_query(user_query)
        pinecone_results = index.query(
            vector=query_embedding,
            filter={"user_id": user_id},
            top_k=5,
            include_metadata=True
        )

        if not pinecone_results['matches']:
            return jsonify({"response": "No relevant content found."}), 200

        # Fetch relevant documents
        relevant_docs = []
        for match in pinecone_results['matches']:
            chunk_id = match['id']
            chunk_data = fetch_text_from_supabase(supabase, chunk_id, user_id)
            if chunk_data:
                relevant_docs.append(chunk_data)

        if relevant_docs:
            combined_text = "\n".join(relevant_docs)
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