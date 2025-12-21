from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.soundboard import bp
from app.models import Soundboard, Sound

@bp.route('/dashboard')
@login_required
def dashboard():
    sbs = Soundboard.get_by_user_id(current_user.id)
    return render_template('soundboard/dashboard.html', title='My Soundboards', soundboards=sbs)

@bp.route('/view/<int:id>')
def view(id):
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('main.index'))
    sounds = s.get_sounds()
    return render_template('soundboard/view.html', title=s.name, soundboard=s, sounds=sounds)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
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
            
        s = Soundboard(name=form.name.data, user_id=current_user.id, icon=icon)
        s.save()
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
    if s.user_id != current_user.id:
        flash('You do not have permission to edit this soundboard.')
        return redirect(url_for('soundboard.dashboard'))
    
    form = SoundboardForm()
    if form.validate_on_submit():
        s.name = form.name.data
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
        flash(f'Soundboard "{s.name}" updated!')
        return redirect(url_for('soundboard.dashboard'))
    elif request.method == 'GET':
        form.name.data = s.name
        form.icon.data = s.icon
    
    # Get sounds for this board
    sounds = s.get_sounds()
    return render_template('soundboard/edit.html', title='Edit Soundboard', form=form, soundboard=s, sounds=sounds)

@bp.route('/<int:id>/upload', methods=['GET', 'POST'])
@login_required
def upload_sound(id):
    from app.soundboard.forms import SoundForm
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    
    s = Soundboard.get_by_id(id)
    if s is None or s.user_id != current_user.id:
        flash('Soundboard not found or permission denied.')
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
    
    # Check board ownership
    s = Soundboard.get_by_id(sound.soundboard_id)
    if s is None or s.user_id != current_user.id:
        flash('Permission denied.')
        return redirect(url_for('soundboard.dashboard'))
    
    sound.delete()
    flash('Sound deleted.')
    return redirect(url_for('soundboard.edit', id=s.id))

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    s = Soundboard.get_by_id(id)
    if s is None:
        flash('Soundboard not found.')
        return redirect(url_for('soundboard.dashboard'))
    if s.user_id != current_user.id:
        flash('You do not have permission to delete this soundboard.')
        return redirect(url_for('soundboard.dashboard'))
    
    s.delete()
    flash('Soundboard deleted.')
    return redirect(url_for('soundboard.dashboard'))
