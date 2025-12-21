from flask import Blueprint

bp = Blueprint('soundboard', __name__, url_prefix='/soundboard')

from app.soundboard import routes
