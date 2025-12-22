from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.auth.routes import admin_required
from app.models import User, Soundboard

@bp.route('/users')
@admin_required
def users():
    users = User.get_all()
    return f"Admin Users Page: {len(users)} users"
