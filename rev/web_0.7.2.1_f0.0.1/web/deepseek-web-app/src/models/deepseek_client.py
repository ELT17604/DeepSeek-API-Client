from flask import jsonify
import requests
import base64
import hashlib
import uuid
from cryptography.fernet import Fernet

class DeepSeekClient:
    DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
    DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

    def __init__(self, api_key):
        self.api_key = api_key
        self.encryption_key = self.get_encryption_key()

    def get_encryption_key(self):
        """基于机器特定信息生成稳定的加密密钥"""
        try:
            machine_id = uuid.getnode()
            key_material = f"deepseek-client-{machine_id}-salt-v1".encode()
            key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
            return key
        except Exception:
            return base64.urlsafe_b64encode(hashlib.sha256(b"default-salt-key").digest())

    def encrypt_api_key(self):
        """加密API密钥"""
        if not self.api_key:
            return None
        try:
            f = Fernet(self.encryption_key)
            return f.encrypt(self.api_key.encode()).decode()
        except Exception as e:
            print(f"加密API密钥时出错: {e}")
            return None

    def decrypt_api_key(self, encrypted_api_key):
        """解密API密钥"""
        if not encrypted_api_key:
            return None
        try:
            f = Fernet(self.encryption_key)
            return f.decrypt(encrypted_api_key.encode()).decode()
        except Exception as e:
            print(f"解密API密钥时出错: {e}")
            return None

    def get_balance(self):
        """获取用户余额"""
        try:
            response = requests.get(self.DEEPSEEK_BALANCE_URL, headers={"Authorization": f"Bearer {self.api_key}"})
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({"error": "无法获取余额"}), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def call_api(self, endpoint, data=None):
        """调用DeepSeek API"""
        url = f"{self.DEEPSEEK_API_BASE_URL_V1}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            if data:
                response = requests.post(url, json=data, headers=headers)
            else:
                response = requests.get(url, headers=headers)
            return response.json(), response.status_code
        except Exception as e:
            return {"error": str(e)}, 500