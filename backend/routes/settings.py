from flask import Blueprint, jsonify, request
from supabase import create_client
import os

bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@bp.route('/app', methods=['GET'])
def get_app_settings():
    try:
        # This could be extended to fetch settings from a database
        return jsonify({
            "app_name": "Recallo",
            "theme_options": ["light", "dark", "system"],
            "default_theme": "system",
            "notification_defaults": {
                "email": True,
                "push": False
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/user/<user_id>', methods=['GET', 'PUT'])
def user_settings(user_id):
    if request.method == 'GET':
        try:
            response = supabase.table('user_settings').select('*').eq('user_id', user_id).execute()
            if response.data:
                return jsonify(response.data[0]), 200
            return jsonify({}), 200  # Return empty settings if none exist
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            # Check if settings exist for user
            existing = supabase.table('user_settings').select('id').eq('user_id', user_id).execute()
            
            if existing.data:
                # Update existing settings
                response = supabase.table('user_settings').update(data).eq('user_id', user_id).execute()
            else:
                # Create new settings
                data['user_id'] = user_id
                response = supabase.table('user_settings').insert(data).execute()
                
            if response.data:
                return jsonify(response.data[0]), 200
            return jsonify({"error": "Failed to save settings"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500