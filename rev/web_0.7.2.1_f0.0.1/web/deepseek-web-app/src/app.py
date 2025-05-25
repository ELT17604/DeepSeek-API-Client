from flask import Flask, render_template, request, jsonify
from src.utils.storage import load_api_key_from_file, save_api_key_to_file, delete_api_key_file
from src.utils.encryption import encrypt_api_key, decrypt_api_key
from src.models.deepseek_client import DeepSeekClient

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/save_key', methods=['POST'])
def save_key():
    api_key = request.json.get('api_key')
    if api_key:
        encrypted_key = encrypt_api_key(api_key)
        if save_api_key_to_file(encrypted_key):
            return jsonify({"status": "success", "message": "API Key saved successfully."}), 200
    return jsonify({"status": "error", "message": "Failed to save API Key."}), 400

@app.route('/api/load_key', methods=['GET'])
def load_key():
    api_key = load_api_key_from_file()
    if api_key:
        return jsonify({"status": "success", "api_key": decrypt_api_key(api_key)}), 200
    return jsonify({"status": "error", "message": "No API Key found."}), 404

@app.route('/api/delete_key', methods=['DELETE'])
def delete_key():
    if delete_api_key_file():
        return jsonify({"status": "success", "message": "API Key deleted successfully."}), 200
    return jsonify({"status": "error", "message": "Failed to delete API Key."}), 400

if __name__ == '__main__':
    app.run(debug=True)