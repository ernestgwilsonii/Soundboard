from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.soundboard import bp
from app.models import Soundboard, Sound

@bp.route('/dashboard')
@login_required
def dashboard():
    sbs = Soundboard.get_by_user_id(current_user.id)
    return render_template('soundboard/dashboard.html', title='My Soundboards', soundboards=sbs)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    from app.soundboard.forms import SoundboardForm
    form = SoundboardForm()
    if form.validate_on_submit():
        s = Soundboard(name=form.name.data, user_id=current_user.id, icon=form.icon.data)
        s.save()
        flash(f'Soundboard "{s.name}" created!')
        return redirect(url_for('soundboard.dashboard'))
    return render_template('soundboard/create.html', title='Create Soundboard', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    from app.soundboard.forms import SoundboardForm
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
        s.icon = form.icon.data
        s.save()
        flash(f'Soundboard "{s.name}" updated!')
        return redirect(url_for('soundboard.dashboard'))
    elif request.method == 'GET':
        form.name.data = s.name
        form.icon.data = s.icon
    return render_template('soundboard/edit.html', title='Edit Soundboard', form=form, soundboard=s)

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
