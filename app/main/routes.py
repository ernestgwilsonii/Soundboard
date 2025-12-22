from flask import render_template
from app.main import bp
from app.models import Soundboard

@bp.route('/')
@bp.route('/index')
def index():
    sbs = Soundboard.get_recent_public(limit=6)
    return render_template('index.html', title='Home', soundboards=sbs)
