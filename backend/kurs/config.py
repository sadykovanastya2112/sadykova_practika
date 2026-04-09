import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    SECRET_KEY= os.getenv('SECRET_KEY', 'super-secret-key')
    AUTHGEAR_CLIENT_SECRET = os.getenv('AUTHGEAR_CLIENT_SECRET')
    AUTHGEAR_CLIENT_ID = os.getenv('AUTHGEAR_CLIENT_ID')
    AUTHGEAR_ISSUER = os.getenv('AUTHGEAR_ISSUER')
    AUTHGEAR_REDIRECT_URI = os.getenv('AUTHGEAR_REDIRECT_URI')
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'flask_session')
    SESSION_COOKIE_DOMAIN = '127.0.0.1'
    YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
    YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

    
