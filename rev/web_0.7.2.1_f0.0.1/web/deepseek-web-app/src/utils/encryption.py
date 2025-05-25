def get_encryption_key():
    """基于机器特定信息生成稳定的加密密钥"""
    try:
        import uuid
        import base64
        import hashlib

        machine_id = uuid.getnode()
        key_material = f"deepseek-client-{machine_id}-salt-v1".encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
        return key
    except Exception:
        return base64.urlsafe_b64encode(hashlib.sha256(b"default-salt-key").digest())

def encrypt_api_key(api_key):
    """加密API密钥"""
    if not api_key:
        return None
    try:
        from cryptography.fernet import Fernet
        key = get_encryption_key()
        f = Fernet(key)
        return f.encrypt(api_key.encode()).decode()
    except Exception as e:
        print(f"加密API密钥时出错: {e}")
        return None

def decrypt_api_key(encrypted_api_key):
    """解密API密钥"""
    if not encrypted_api_key:
        return None
    try:
        from cryptography.fernet import Fernet
        key = get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_api_key.encode()).decode()
    except Exception as e:
        print(f"解密API密钥时出错: {e}")
        return None