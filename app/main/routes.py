from flask import render_template, jsonify, request, abort
from flask_login import current_user
from app.main import bp
from app.models import Soundboard, User, AdminSettings

@bp.app_context_processor
def inject_announcement():
    return {
        'announcement_message': AdminSettings.get_setting('announcement_message'),
        'announcement_type': AdminSettings.get_setting('announcement_type') or 'info'
    }

@bp.before_app_request
def check_maintenance():
    # Allow static files and auth routes (login/logout)
    if request.path.startswith('/static') or request.path.startswith('/auth'):
        return
        
    is_maintenance = AdminSettings.get_setting('maintenance_mode') == '1'
    if is_maintenance:
        # Admins bypass maintenance
        if current_user.is_authenticated and current_user.role == 'admin':
            return
        
        # Check if already on maintenance page to avoid loop (if we were redirecting)
        # But here we will render template directly or abort
        # If we use render_template, we need to return it.
        # before_app_request needs to return None to continue, or a response to stop.
        return render_template('maintenance.html'), 503

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
    my_playlists = []
    
    if current_user.is_authenticated:
        from app.models import Playlist
        my_boards = [
            {'id': sb.id, 'name': sb.name, 'icon': sb.icon} 
            for sb in Soundboard.get_by_user_id(current_user.id)
        ]
        
        fav_ids = current_user.get_favorites()
        for fid in fav_ids:
            sb = Soundboard.get_by_id(fid)
            if sb:
                favorites.append({'id': sb.id, 'name': sb.name, 'icon': sb.icon})

        my_playlists = [
            {'id': pl.id, 'name': pl.name} 
            for pl in Playlist.get_by_user_id(current_user.id)
        ]
    
    # ...
    return jsonify({
        'my_boards': my_boards,
        'favorites': favorites,
        'my_playlists': my_playlists,
        'explore': explore
    })
