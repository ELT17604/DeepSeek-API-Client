from flask import Blueprint, request, jsonify
from ..models.deepseek_client import DeepSeekClient
from ..utils.storage import load_api_key_from_file, save_api_key_to_file, delete_api_key_file
from ..utils.encryption import encrypt_api_key, decrypt_api_key

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/init', methods=['POST'])
def initialize_client():
    api_key = request.json.get('api_key')
    if api_key:
        encrypted_key = encrypt_api_key(api_key)
        if save_api_key_to_file(encrypted_key):
            return jsonify({"message": "API Key saved and client initialized."}), 200
        else:
            return jsonify({"error": "Failed to save API Key."}), 500
    return jsonify({"error": "API Key is required."}), 400

@api_bp.route('/api/models', methods=['GET'])
def get_models():
    client = DeepSeekClient()
    models = client.get_available_models()
    return jsonify(models), 200

@api_bp.route('/api/balance', methods=['GET'])
def get_balance():
    client = DeepSeekClient()
    balance = client.get_balance()
    return jsonify({"balance": balance}), 200

@api_bp.route('/api/delete_key', methods=['DELETE'])
def delete_key():
    if delete_api_key_file():
        return jsonify({"message": "API Key deleted."}), 200
    return jsonify({"error": "Failed to delete API Key."}), 500

@api_bp.route('/api/decrypt_key', methods=['GET'])
def decrypt_key():
    encrypted_key = load_api_key_from_file()
    if encrypted_key:
        decrypted_key = decrypt_api_key(encrypted_key)
        return jsonify({"api_key": decrypted_key}), 200
    return jsonify({"error": "No API Key found."}), 404