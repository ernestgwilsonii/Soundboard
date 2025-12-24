from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.auth.routes import admin_required
from app.models import User, Soundboard, AdminSettings

@bp.route('/users')
@admin_required
def users():
    users_list = User.get_all()
    return render_template('admin/users.html', title='User Management', users=users_list)

@bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    from app.admin.forms import PlatformSettingsForm
    form = PlatformSettingsForm()
    if form.validate_on_submit():
        AdminSettings.set_setting('featured_soundboard_id', form.featured_soundboard_id.data)
        AdminSettings.set_setting('announcement_message', form.announcement_message.data)
        AdminSettings.set_setting('announcement_type', form.announcement_type.data)
        AdminSettings.set_setting('maintenance_mode', '1' if form.maintenance_mode.data else '0')
        flash('Settings updated.')
        return redirect(url_for('admin.settings'))
    elif request.method == 'GET':
        form.featured_soundboard_id.data = AdminSettings.get_setting('featured_soundboard_id')
        form.announcement_message.data = AdminSettings.get_setting('announcement_message')
        form.announcement_type.data = AdminSettings.get_setting('announcement_type') or 'info'
        form.maintenance_mode.data = (AdminSettings.get_setting('maintenance_mode') == '1')
    
    return render_template('admin/settings.html', title='Admin Settings', form=form)

@bp.route('/soundboards')
@admin_required
def soundboards():
    sbs = Soundboard.get_all()
    return render_template('admin/soundboards.html', title='Content Management', soundboards=sbs)

@bp.route('/user/<int:id>/toggle_active', methods=['POST'])
@admin_required
def toggle_user_active(id):
    u = User.get_by_id(id)
    if u is None:
        flash('User not found.')
        return redirect(url_for('admin.users'))
    if u.id == current_user.id:
        flash('You cannot disable your own account!')
        return redirect(url_for('admin.users'))
    
    u.active = not u.active
    u.save()
    status = "enabled" if u.active else "disabled"
    flash(f'User {u.username} has been {status}.')
    return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/toggle_role', methods=['POST'])
@admin_required
def toggle_user_role(id):
    u = User.get_by_id(id)
    if u is None:
        flash('User not found.')
        return redirect(url_for('admin.users'))
    if u.id == current_user.id:
        flash('You cannot change your own role!')
        return redirect(url_for('admin.users'))
    
    u.role = 'admin' if u.role == 'user' else 'user'
    u.save()
    flash(f'User {u.username} role changed to {u.role}.')
    return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/reset_password', methods=['GET', 'POST'])
@admin_required
def reset_password(id):
    from app.admin.forms import AdminPasswordResetForm
    u = User.get_by_id(id)
    if u is None:
        flash('User not found.')
        return redirect(url_for('admin.users'))
    
    form = AdminPasswordResetForm()
    if form.validate_on_submit():
        u.set_password(form.password.data)
        u.save()
        flash(f'Password for {u.username} has been reset.')
        return redirect(url_for('admin.users'))
    return render_template('admin/reset_password.html', title='Reset Password', form=form, user=u)

@bp.route('/user/<int:id>/update_email', methods=['GET', 'POST'])
@admin_required
def update_email(id):
    from app.admin.forms import AdminUpdateEmailForm
    u = User.get_by_id(id)
    if u is None:
        flash('User not found.')
        return redirect(url_for('admin.users'))
    
    form = AdminUpdateEmailForm(user_id=u.id)
    if form.validate_on_submit():
        u.email = form.email.data
        u.save()
        flash(f'Email for {u.username} has been updated.')
        return redirect(url_for('admin.users'))
    elif request.method == 'GET':
        form.email.data = u.email
    return render_template('admin/update_email.html', title='Update Email', form=form, user=u)
