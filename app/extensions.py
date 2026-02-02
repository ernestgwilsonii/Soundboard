"""Extensions module.

Initializes Flask extensions used across the application.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config

# Initialize extensions
login = LoginManager()
login.login_view = "auth.login"
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    message_queue=Config.SOCKETIO_MESSAGE_QUEUE,
)
db_orm = SQLAlchemy()
migrate = Migrate(render_as_batch=True, multidb=True)
