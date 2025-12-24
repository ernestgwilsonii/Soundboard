from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.soundboard import bp
from app.models import Soundboard, Sound
from app.db import get_soundboards_db
from app.auth.routes import verification_required
from app import limiter

@bp.route('/dashboard')
@login_required
def dashboard():
    sbs = Soundboard.get_by_user_id(current_user.id)
    return render_template('soundboard/dashboard.html', title='My Soundboards', soundboards=sbs)

@bp.route('/view/<int:id>')
def view(id):
    from flask_login import current_user
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('main.index'))
    
    # Access control: Private boards only accessible by owner
    if not s.is_public:
        if not current_user.is_authenticated or s.user_id != current_user.id:
            flash('This soundboard is private.')
            return redirect(url_for('main.index'))
    
    is_favorite = False
    if current_user.is_authenticated:
        favorites = current_user.get_favorites()
        if s.id in favorites:
            is_favorite = True
            
    sounds = s.get_sounds()
    return render_template('soundboard/view.html', title=s.name, soundboard=s, sounds=sounds, is_favorite=is_favorite)

@bp.route('/<int:id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(id):
    from flask import jsonify
    s = Soundboard.get_by_id(id)
    if s is None:
        return jsonify({'error': 'Soundboard not found'}), 404
    
    if not s.is_public:
        return jsonify({'error': 'Cannot favorite private soundboards'}), 403
        
    favorites = current_user.get_favorites()
    if s.id in favorites:
        current_user.remove_favorite(s.id)
        is_favorite = False
    else:
        current_user.add_favorite(s.id)
        is_favorite = True
        
    return jsonify({'is_favorite': is_favorite})

@bp.route('/<int:id>/rate', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def rate_board(id):
    from flask import jsonify
    from app.models import Rating
    s = Soundboard.get_by_id(id)
    if s is None:
        return jsonify({'error': 'Soundboard not found'}), 404
    
    if not s.is_public:
        return jsonify({'error': 'Cannot rate private soundboards'}), 403
        
    data = request.get_json()
    if not data or 'score' not in data:
        return jsonify({'error': 'Score required'}), 400
        
    score = int(data['score'])
    if score < 1 or score > 5:
        return jsonify({'error': 'Score must be between 1 and 5'}), 400
        
    rating = Rating(user_id=current_user.id, soundboard_id=s.id, score=score)
    rating.save()
    
    stats = s.get_average_rating()
    return jsonify({
        'status': 'success',
        'average': stats['average'],
        'count': stats['count']
    })

@bp.route('/<int:id>/comment', methods=['POST'])
@verification_required
@limiter.limit("10 per minute")
def post_comment(id):
    from app.soundboard.forms import CommentForm
    from app.models import Comment
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('main.index'))
    
    if not s.is_public:
        flash('Cannot comment on private soundboards.')
        return redirect(url_for('main.index'))
        
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(user_id=current_user.id, soundboard_id=s.id, text=form.text.data)
        comment.save()
        flash('Comment posted!')
    
    return redirect(url_for('soundboard.view', id=s.id))

@bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    from app.models import Comment
    comment = Comment.get_by_id(id)
    if comment is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
        
    s = Soundboard.get_by_id(comment.soundboard_id)
    
    # Permission check: Author OR Board Owner OR Admin
    if (comment.user_id != current_user.id and 
        s.user_id != current_user.id and 
        current_user.role != 'admin'):
        flash('Permission denied.')
        return redirect(url_for('soundboard.view', id=s.id))
        
    comment.delete()
    flash('Comment deleted.')
    return redirect(url_for('soundboard.view', id=s.id))

@bp.route('/<int:id>/reorder', methods=['POST'])
@login_required
def reorder_sounds(id):
    from flask import jsonify
    s = Soundboard.get_by_id(id)
    if s is None:
        return jsonify({'error': 'Soundboard not found'}), 404
        
    if s.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
        
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({'error': 'Invalid data'}), 400
        
    sound_ids = data['ids']
    db = get_soundboards_db()
    cur = db.cursor()
    
    try:
        for index, sound_id in enumerate(sound_ids):
            cur.execute(
                "UPDATE sounds SET display_order = ? WHERE id = ? AND soundboard_id = ?",
                (index + 1, sound_id, s.id)
            )
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
        
    return jsonify({'status': 'success'})

@bp.route('/gallery')
def gallery():
    sbs = Soundboard.get_public()
    return render_template('soundboard/gallery.html', title='Public Gallery', soundboards=sbs)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        sbs = Soundboard.search(query)
    else:
        sbs = []
    return render_template('soundboard/search.html', title='Search Results', soundboards=sbs, query=query)

@bp.route('/create', methods=['GET', 'POST'])
@verification_required
def create():
    from app.soundboard.forms import SoundboardForm
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    form = SoundboardForm()
    if form.validate_on_submit():
        icon = form.icon.data
        if form.icon_image.data:
            f = form.icon_image.data
            filename = secure_filename(f.filename)
            icon_path = os.path.join('icons', filename)
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], icon_path)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            f.save(full_path)
            icon = icon_path
            
        s = Soundboard(name=form.name.data, user_id=current_user.id, icon=icon, is_public=form.is_public.data, theme_color=form.theme_color.data)
        s.save()
        
        # Process tags
        if form.tags.data:
            tag_list = [t.strip() for t in form.tags.data.split(',') if t.strip()]
            for tag_name in tag_list:
                s.add_tag(tag_name)
        
        from app.models import Activity
        Activity.record(current_user.id, 'create_soundboard', f'Created a new soundboard: "{s.name}"')
                
        flash(f'Soundboard "{s.name}" created!')
        return redirect(url_for('soundboard.dashboard'))
    return render_template('soundboard/create.html', title='Create Soundboard', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    from app.soundboard.forms import SoundboardForm
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('soundboard.dashboard'))
    
    # Ownership check with admin override
    if s.user_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to edit this soundboard.')
        return redirect(url_for('soundboard.dashboard'))
    
    form = SoundboardForm()
    if form.validate_on_submit():
        s.name = form.name.data
        s.is_public = form.is_public.data
        s.theme_color = form.theme_color.data
        if form.icon_image.data:
            f = form.icon_image.data
            filename = secure_filename(f.filename)
            icon_path = os.path.join('icons', filename)
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], icon_path)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            f.save(full_path)
            s.icon = icon_path
        else:
            s.icon = form.icon.data
        s.save()
        
        # Process tags (replace existing)
        current_tags = [t.name for t in s.get_tags()]
        new_tags = [t.strip().lower() for t in form.tags.data.split(',') if t.strip()] if form.tags.data else []
        
        for nt in new_tags:
            if nt not in current_tags:
                s.add_tag(nt)
        
        for ct in current_tags:
            if ct not in new_tags:
                s.remove_tag(ct)
                
        flash(f'Soundboard "{s.name}" updated!')
        return redirect(url_for('soundboard.dashboard'))
    elif request.method == 'GET':
        form.name.data = s.name
        form.icon.data = s.icon
        form.is_public.data = s.is_public
        form.theme_color.data = s.theme_color
        form.tags.data = ", ".join([t.name for t in s.get_tags()])
    
    # Get sounds for this board
    sounds = s.get_sounds()
    return render_template('soundboard/edit.html', title='Edit Soundboard', form=form, soundboard=s, sounds=sounds)

@bp.route('/<int:id>/upload', methods=['GET', 'POST'])
@verification_required
@limiter.limit("5 per minute")
def upload_sound(id):
    from app.soundboard.forms import SoundForm
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('soundboard.dashboard'))
        
    # Ownership check with admin override
    if s.user_id != current_user.id and current_user.role != 'admin':
        flash('Permission denied.')
        return redirect(url_for('soundboard.dashboard'))
    
    form = SoundForm()
    if form.validate_on_submit():
        f = form.audio_file.data
        filename = secure_filename(f.filename)
        
        # Create directory for soundboard if it doesn't exist
        sb_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(s.id))
        if not os.path.exists(sb_dir):
            os.makedirs(sb_dir)
            
        file_path = os.path.join(str(s.id), filename)
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        f.save(full_path)
        
        icon = form.icon.data
        if form.icon_image.data:
            fi = form.icon_image.data
            iname = secure_filename(fi.filename)
            icon_path = os.path.join('icons', iname)
            if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], 'icons')):
                os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], 'icons'))
            fi.save(os.path.join(current_app.config['UPLOAD_FOLDER'], icon_path))
            icon = icon_path
            
        sound = Sound(soundboard_id=s.id, name=form.name.data, file_path=file_path, icon=icon)
        sound.save()
        
        from app.models import Activity
        Activity.record(current_user.id, 'upload_sound', f'Uploaded sound "{sound.name}" to "{s.name}"')
        
        flash(f'Sound "{sound.name}" uploaded!')
        return redirect(url_for('soundboard.edit', id=s.id))
    
    return render_template('soundboard/upload.html', title='Upload Sound', form=form, soundboard=s)

@bp.route('/sound/<int:id>/delete', methods=['POST'])
@login_required
def delete_sound(id):
    sound = Sound.get_by_id(id)
    if sound is None:
        flash('Sound not found.')
        return redirect(url_for('soundboard.dashboard'))
    
    # Check board ownership with admin override
    s = Soundboard.get_by_id(sound.soundboard_id)
    if s is None or (s.user_id != current_user.id and current_user.role != 'admin'):
        flash('Permission denied.')
        return redirect(url_for('soundboard.dashboard'))
    
    sound.delete()
    flash('Sound deleted.')
    return redirect(url_for('soundboard.edit', id=s.id))

@bp.route('/sound/<int:id>/settings', methods=['POST'])
@login_required
def update_sound_settings(id):
    from flask import jsonify
    sound = Sound.get_by_id(id)
    if sound is None:
        return jsonify({'error': 'Sound not found'}), 404
        
    s = Soundboard.get_by_id(sound.soundboard_id)
    if s.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    sound.volume = data.get('volume', sound.volume)
    sound.is_loop = data.get('is_loop', sound.is_loop)
    sound.start_time = data.get('start_time', sound.start_time)
    sound.end_time = data.get('end_time', sound.end_time)
    
    sound.save()
    return jsonify({'status': 'success'})

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('soundboard.dashboard'))
    
    # Ownership check with admin override
    if s.user_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this soundboard.')
        return redirect(url_for('soundboard.dashboard'))
    
    s.delete()
    flash('Soundboard deleted.')
    return redirect(url_for('soundboard.dashboard'))

# Playlist Routes
@bp.route('/playlists')
@login_required
def playlists():
    from app.models import Playlist
    user_playlists = Playlist.get_by_user_id(current_user.id)
    return render_template('soundboard/playlists.html', title='My Playlists', playlists=user_playlists)

@bp.route('/playlist/create', methods=['GET', 'POST'])
@login_required
def create_playlist():
    from app.soundboard.forms import PlaylistForm
    from app.models import Playlist
    form = PlaylistForm()
    if form.validate_on_submit():
        pl = Playlist(user_id=current_user.id, name=form.name.data, 
                      description=form.description.data, is_public=form.is_public.data)
        pl.save()
        flash(f'Playlist "{pl.name}" created!')
        return redirect(url_for('soundboard.playlists'))
    return render_template('soundboard/create_playlist.html', title='Create Playlist', form=form)

@bp.route('/playlist/<int:playlist_id>/add/<int:sound_id>', methods=['POST'])
@login_required
def add_to_playlist(playlist_id, sound_id):
    from flask import jsonify
    from app.models import Playlist, Sound
    pl = Playlist.get_by_id(playlist_id)
    if pl is None:
        return jsonify({'error': 'Playlist not found'}), 404
        
    if pl.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
        
    sound = Sound.get_by_id(sound_id)
    if sound is None:
        return jsonify({'error': 'Sound not found'}), 404
        
    # Check if sound is accessible (own board or public)
    s = Soundboard.get_by_id(sound.soundboard_id)
    if not s.is_public and s.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Sound is private'}), 403
        
    pl.add_sound(sound.id)
    return jsonify({'status': 'success'})

@bp.route('/playlist/<int:id>')
def view_playlist(id):
    from app.models import Playlist
    pl = Playlist.get_by_id(id)
    if pl is None:
        flash('Playlist not found.')
        return redirect(url_for('main.index'))
    
    if not pl.is_public:
        if not current_user.is_authenticated or pl.user_id != current_user.id:
            flash('This playlist is private.')
            return redirect(url_for('main.index'))
            
    sounds = pl.get_sounds()
    return render_template('soundboard/view_playlist.html', title=pl.name, playlist=pl, sounds=sounds)

@bp.route('/playlist/<int:id>/delete', methods=['POST'])
@login_required
def delete_playlist(id):
    from app.models import Playlist
    pl = Playlist.get_by_id(id)
    if pl is None:
        flash('Playlist not found.')
        return redirect(url_for('soundboard.playlists'))
    
    if pl.user_id != current_user.id and current_user.role != 'admin':
        flash('Permission denied.')
        return redirect(url_for('soundboard.playlists'))
        
    pl.delete()
    flash('Playlist deleted.')
    return redirect(url_for('soundboard.playlists'))

@bp.route('/tag/<tag_name>')
def tag_search(tag_name):
    from app.models import Tag, Soundboard
    sbs = Soundboard.get_by_tag(tag_name)
    return render_template('soundboard/search.html', title=f'Tag: {tag_name}', soundboards=sbs, query=tag_name)