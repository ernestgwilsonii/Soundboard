from flask import render_template, jsonify
from flask_login import current_user
from app.main import bp
from app.models import Soundboard, User, AdminSettings

@bp.app_context_processor
def inject_announcement():
    return {
        'announcement_message': AdminSettings.get_setting('announcement_message'),
        'announcement_type': AdminSettings.get_setting('announcement_type') or 'info'
    }

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

@bp.route('/sidebar-data')
def sidebar_data():
    my_boards = []
    favorites = []
    
    if current_user.is_authenticated:
        my_boards = [
            {'id': sb.id, 'name': sb.name, 'icon': sb.icon} 
            for sb in Soundboard.get_by_user_id(current_user.id)
        ]
        
        fav_ids = current_user.get_favorites()
        for fid in fav_ids:
            sb = Soundboard.get_by_id(fid)
            if sb:
                favorites.append({'id': sb.id, 'name': sb.name, 'icon': sb.icon})
    
    # Explore section: All public boards grouped by user
    public_boards = Soundboard.get_public()
    explore = {}
    for sb in public_boards:
        creator = sb.get_creator_username()
        if creator not in explore:
            explore[creator] = []
        explore[creator].append({'id': sb.id, 'name': sb.name, 'icon': sb.icon})
                
    return jsonify({
        'my_boards': my_boards,
        'favorites': favorites,
        'explore': explore
    })
