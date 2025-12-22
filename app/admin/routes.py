from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.auth.routes import admin_required
from app.models import User, Soundboard

@bp.route('/users')
@admin_required
def users():
    users_list = User.get_all()
    return render_template('admin/users.html', title='User Management', users=users_list)

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
