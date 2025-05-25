from flask import Blueprint, request, jsonify, render_template
from src.utils.storage import load_api_key_from_file, save_api_key_to_file
from src.utils.encryption import encrypt_api_key, decrypt_api_key
from src.models.deepseek_client import DeepSeekClient

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['GET'])
def chat():
    return render_template('index.html')

@chat_bp.route('/api/init', methods=['POST'])
def initialize_client():
    api_key = request.json.get('api_key')
    if api_key:
        encrypted_key = encrypt_api_key(api_key)
        if save_api_key_to_file(encrypted_key):
            client = DeepSeekClient(api_key)
            return jsonify({"status": "success", "message": "Client initialized."}), 200
    return jsonify({"status": "error", "message": "Failed to initialize client."}), 400

@chat_bp.route('/api/models', methods=['GET'])
def get_models():
    client = DeepSeekClient(load_api_key_from_file())
    models = client.get_available_models()
    return jsonify(models), 200

@chat_bp.route('/api/chat', methods=['POST'])
def chat_with_model():
    user_input = request.json.get('input')
    model = request.json.get('model')
    client = DeepSeekClient(load_api_key_from_file())
    response = client.chat(user_input, model)
    return jsonify({"response": response}), 200