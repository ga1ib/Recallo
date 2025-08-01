from flask import Blueprint, jsonify, request
from supabase import create_client
import os

users_bp = Blueprint('users', __name__, url_prefix='/api/users')
bp = users_bp  # Alias for backward compatibility

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        response = supabase.table('users').select(
            'id, email, name, created_at'
        ).eq('id', user_id).execute()
        
        if not response.data:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(response.data[0]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<user_id>/documents', methods=['GET'])
def get_user_documents(user_id):
    try:
        response = supabase.table('documents').select(
            'id, file_name, created_at, summary'
        ).eq('user_id', user_id).execute()
        
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<user_id>/settings', methods=['PUT'])
def update_user_settings(user_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update user settings
        response = supabase.table('users').update(data).eq('id', user_id).execute()
        
        if response.data:
            return jsonify(response.data[0]), 200
        else:
            return jsonify({"error": "Failed to update user settings"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500