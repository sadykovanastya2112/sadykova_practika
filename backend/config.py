import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    SECRET_KEY= os.getenv('SECRET_KEY', 'super-secret-key')
    LOGTO_CLIENT_ID  = os.getenv('LOGTO_CLIENT_ID')
    LOGTO_CLIENT_SECRET = os.getenv('LOGTO_CLIENT_SECRET')
    LOGTO_ISSUER = os.getenv('LOGTO_ISSUER')
    LOGTO_REDIRECT_URI = os.getenv('LOGTO_REDIRECT_URI')
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'flask_session')
    SESSION_COOKIE_DOMAIN = '127.0.0.1'
    YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
    YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    
