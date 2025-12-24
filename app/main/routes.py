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
    popular_tags = []
    
    if current_user.is_authenticated:
        from app.models import Playlist, Tag
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
        
        popular_tags = [
            {'name': t.name} for t in Tag.get_popular(limit=10)
        ]
    else:
        from app.models import Tag
        popular_tags = [
            {'name': t.name} for t in Tag.get_popular(limit=10)
        ]
    
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
        'my_playlists': my_playlists,
        'popular_tags': popular_tags,
        'explore': explore
    })