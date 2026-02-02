import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    DEBUG = os.environ.get("DEBUG", "False").lower() in ["true", "1", "t"]
    TESTING = os.environ.get("TESTING", "False").lower() in ["true", "1", "t"]

    # Database paths
    ACCOUNTS_DB = os.environ.get("ACCOUNTS_DB") or os.path.join(
        basedir, "accounts.sqlite3"
    )
    SOUNDBOARDS_DB = os.environ.get("SOUNDBOARDS_DB") or os.path.join(
        basedir, "soundboards.sqlite3"
    )

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    USE_REDIS_QUEUE = os.environ.get("USE_REDIS_QUEUE", "False").lower() in [
        "true",
        "1",
        "t",
    ]
    SOCKETIO_MESSAGE_QUEUE = REDIS_URL if USE_REDIS_QUEUE else None

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI"
    ) or "sqlite:///" + os.path.abspath(ACCOUNTS_DB)

    SQLALCHEMY_BINDS = {
        "soundboards": os.environ.get("SQLALCHEMY_BINDS_SOUNDBOARDS")
        or "sqlite:///" + os.path.abspath(SOUNDBOARDS_DB)
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = os.environ.get("WTF_CSRF_ENABLED", "True").lower() in [
        "true",
        "1",
        "t",
    ]

    # Email settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Sound file storage
    SOUNDS_DIR = os.path.join(basedir, "app", "static", "uploads")
    UPLOAD_FOLDER = SOUNDS_DIR
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit
    ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg"}
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
