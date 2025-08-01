from flask import Blueprint, send_from_directory
import os

files_bp = Blueprint('files', __name__)
bp = files_bp  # Alias for backward compatibility

@bp.route('/uploads/<filename>', methods=['GET'])
def serve_uploaded_file(filename):
    upload_folder = 'uploads'
    return send_from_directory(upload_folder, filename)

@bp.route('/exports/<filename>', methods=['GET'])
def serve_exported_file(filename):
    export_folder = 'exports'
    return send_from_directory(export_folder, filename)