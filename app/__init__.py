"""
Main application package initialization.

This module sets up the Flask application, initializes extensions (Login, CSRF, Mail, Limiter, SocketIO),
and registers blueprints and error handlers.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from flask import Flask, render_template

from app.enums import UserRole
from app.extensions import csrf, db_orm, limiter, login, mail, migrate, socketio
from config import Config


@login.user_loader  # type: ignore
def load_user(id: str) -> Any:
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


def create_app(config_class: Any = Config) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_class (class): The configuration class to use.

    Returns:
        Flask: The configured Flask application instance.
    """
    flask_app = Flask(__name__, template_folder="../templates")
    flask_app.config.from_object(config_class)

    # Initialize Flask extensions
    login.init_app(flask_app)
    csrf.init_app(flask_app)
    mail.init_app(flask_app)
    limiter.init_app(flask_app)
    socketio.init_app(flask_app)
    db_orm.init_app(flask_app)
    migrate.init_app(flask_app, db_orm)

    # Bypass rate limiting for admins and testing
    @limiter.request_filter  # type: ignore
    def admin_whitelist() -> bool:
        from flask_login import current_user

        if flask_app.config.get("TESTING"):
            return True
        return bool(
            current_user.is_authenticated and current_user.role == UserRole.ADMIN
        )

    # Initialize legacy SQLite connection handler
    import app.db as legacy_db

    legacy_db.init_app(flask_app)

    @flask_app.context_processor  # type: ignore
    def inject_enums() -> Dict[str, Any]:
        return {"UserRole": UserRole}

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
    @flask_app.errorhandler(404)  # type: ignore
    def not_found_error(error: Any) -> Any:
        return render_template("404.html"), 404

    @flask_app.errorhandler(500)  # type: ignore
    def internal_error(error: Any) -> Any:
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
import app.socket_events  # noqa: F401, E402
