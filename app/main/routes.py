from flask import render_template
from app.main import bp
from app.models import Soundboard

@bp.route('/')
@bp.route('/index')
def index():
    featured = Soundboard.get_featured()
    recent_all = Soundboard.get_recent_public(limit=7)
    
    # Filter out featured from recent list to avoid duplication
    if featured:
        soundboards = [sb for sb in recent_all if sb.id != featured.id][:6]
    else:
        soundboards = recent_all[:6]
        
    return render_template('index.html', title='Home', featured=featured, soundboards=soundboards)
