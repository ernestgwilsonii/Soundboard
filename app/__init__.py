import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

login = LoginManager()
login.login_view = 'auth.login'
csrf = CSRFProtect()

@login.user_loader
def load_user(id):
    from app.models import User
    return User.get_by_id(int(id))

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(config_class)

    # Initialize Flask extensions here (if any)
    login.init_app(app)
    csrf.init_app(app)
    
    from app import db
    db.init_app(app)

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.soundboard import bp as soundboard_bp
    app.register_blueprint(soundboard_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/soundboard.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Soundboard startup')

    return app
