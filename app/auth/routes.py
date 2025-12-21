from flask import render_template, redirect, url_for, flash
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm

@bp.route('/login', methods=['GET', 'POST'])
def login():
    return "Login Page"

@bp.route('/logout')
def logout():
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    return "Register Page"
