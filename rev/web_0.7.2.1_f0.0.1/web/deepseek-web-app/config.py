import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'
    DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
    DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"
    API_KEY_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "API_KEY")