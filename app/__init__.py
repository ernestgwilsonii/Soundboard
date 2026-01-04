"""
Main application package initialization.

This module sets up the Flask application, initializes extensions (Login, CSRF, Mail, Limiter, SocketIO),
and registers blueprints and error handlers.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect

from config import Config

login = LoginManager()
login.login_view = "auth.login"
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


@login.user_loader
def load_user(id):
    """
    Load a user given the ID.

    Args:
        id (str): The user ID (as a string).

    Returns:
        User: The user object, or None if not found.
    """
    from flask import current_app

    from app.models import User

    user = User.get_by_id(int(id))
    if user and not user.is_verified and current_app.config.get("TESTING"):
        # Force a fresh DB check for verification status during tests
        fresh_user = User.get_by_id(int(id))
        if fresh_user and fresh_user.is_verified:
            user.is_verified = True
    return user


def create_app(config_class=Config):
    """
    Create and configure the Flask application.

    Args:
        config_class (class): The configuration class to use.

    Returns:
        Flask: The configured Flask application instance.
    """
    flask_app = Flask(__name__, template_folder="../templates")
    flask_app.config.from_object(config_class)

    # Initialize Flask extensions here (if any)
    login.init_app(flask_app)
    csrf.init_app(flask_app)
    mail.init_app(flask_app)
    limiter.init_app(flask_app)
    socketio.init_app(flask_app)

    # Bypass rate limiting for admins and testing
    @limiter.request_filter
    def admin_whitelist():
        from flask_login import current_user

        if flask_app.config.get("TESTING"):
            return True
        return current_user.is_authenticated and current_user.role == "admin"

    from app import db

    db.init_app(flask_app)

    # Register blueprints here
    from app.main import bp as main_bp

    flask_app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp

    flask_app.register_blueprint(auth_bp)

    from app.soundboard import bp as soundboard_bp

    flask_app.register_blueprint(soundboard_bp)

    from app.admin import bp as admin_bp

    flask_app.register_blueprint(admin_bp)

    # Error Handlers
    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @flask_app.errorhandler(500)
    def internal_error(error):
        from app.db import close_db

        close_db()  # Ensure DB connection is closed on error
        return render_template("500.html"), 500

    # Configure logging
    if not flask_app.debug and not flask_app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/soundboard.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        flask_app.logger.addHandler(file_handler)

        flask_app.logger.setLevel(logging.INFO)
        flask_app.logger.info("Soundboard startup")

    return flask_app


# Register socket events
import app.socket_events
