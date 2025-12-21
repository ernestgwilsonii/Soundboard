from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.soundboard import bp
from app.models import Soundboard, Sound

@bp.route('/dashboard')
@login_required
def dashboard():
    return "User Dashboard"

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    return "Create Soundboard"

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    return f"Edit Soundboard {id}"

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    return f"Delete Soundboard {id}"
