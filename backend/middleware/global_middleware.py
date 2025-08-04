# middleware/global_middleware.py
from flask import request, jsonify

def validate_json_keys(required_keys):
    def middleware():
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400

            missing = [key for key in required_keys if key not in data]
            if missing:
                return jsonify({"error": f"Missing keys: {', '.join(missing)}"}), 400
    return middleware
