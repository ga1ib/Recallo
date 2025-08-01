from flask import Blueprint, request, jsonify, abort
import logging
import uuid
import os
from supabase import create_client

# Create blueprint
conversations_bp = Blueprint('conversations', __name__)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

        # Update the conversation's updated_at timestamp
        supabase.table("conversations").update({
            "updated_at": "now()"
        }).eq("conversation_id", conv_id).execute()

        logging.info(f"Inserted chat log into Supabase for conversation {conv_id}")
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"Supabase insert error: {e}")
        return None

@conversations_bp.route("/api/conversations", methods=["GET", "POST"])
def conversations():
    if request.method == "GET":
        # List all conversations for a user
        user_id = request.args.get("user_id")
        if not user_id:
            abort(400, "Missing user_id")

        try:
            response = supabase.table("conversations").select(
                "conversation_id, title, created_at, updated_at"
            ).eq("user_id", user_id).order("updated_at", desc=True).execute()
            return jsonify(response.data), 200
        except Exception as e:
            logging.error(f"Error fetching conversations: {e}")
            abort(500, "Failed to fetch conversations")

    elif request.method == "POST":
        # Create a new conversation
        data = request.get_json() or {}
        user_id = data.get("user_id")
        title = data.get("title", "New Chat")

        if not user_id:
            abort(400, "Missing user_id in body")

        # Generate unique conversation_id
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

@conversations_bp.route("/api/conversations/<conversation_id>", methods=["PUT"])
def rename_conversation(conversation_id):
    """Rename a conversation"""
    data = request.get_json()
    new_title = data.get("title")

    if not new_title:
        return jsonify({"error": "Title is required"}), 400

    try:
        response = supabase.table("conversations").update({
            "title": new_title,
            "updated_at": "now()"
        }).eq("conversation_id", conversation_id).execute()

        return jsonify({"message": "Conversation renamed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        # Delete chat logs first
        supabase.table("chat_logs").delete().eq("conversation_id", conversation_id).execute()

        # Then delete the conversation
        response = supabase.table("conversations").delete().eq("conversation_id", conversation_id).execute()

        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route("/api/conversations/<conv_id>/logs", methods=["GET", "POST"])
def conversation_logs(conv_id):
    """Get or add logs for a specific conversation"""
    # Validate conv_id format
    try:
        uuid.UUID(conv_id)
    except ValueError:
        abort(400, "Invalid conversation_id")

    if request.method == "GET":
        # Fetch all logs for this conversation
        try:
            response = supabase.table("chat_logs").select(
                "id, user_message, response_message, created_at"
            ).eq("conversation_id", conv_id).order("created_at", desc=False).execute()
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