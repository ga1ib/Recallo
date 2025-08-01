from flask import Blueprint, jsonify
from supabase import create_client
import os

health_bp = Blueprint('health', __name__)
bp = health_bp  # Alias for backward compatibility

@bp.route('/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Simple query to test connection
        response = supabase.table('users').select('user_id').limit(1).execute()
        
        if response.data is not None:
            return jsonify({
                "status": "healthy",
                "database": "connected"
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "database": "connection failed"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500