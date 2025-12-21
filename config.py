import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 't']
    
    # Database paths
    ACCOUNTS_DB = os.path.join(basedir, 'accounts.sqlite3')
    SOUNDBOARDS_DB = os.path.join(basedir, 'soundboards.sqlite3')
    
    # Sound file storage
    SOUNDS_DIR = os.path.join(basedir, 'sounds')
    UPLOAD_FOLDER = SOUNDS_DIR
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}
