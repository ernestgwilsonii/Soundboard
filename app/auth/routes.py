from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from functools import wraps
from app import limiter

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_verified:
            flash('Please verify your email address to access this feature.')
            return redirect(url_for('auth.profile'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    from flask import request
    from flask_login import current_user, login_user
    from urllib.parse import urlparse
    from app.models import User
    # flash('TEST LOGIN FLASH') # Temporary test
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user is None:
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
            
        if user.is_locked():
            flash(f'Account is locked due to too many failed attempts. Please try again after {user.lockout_until}.')
            return redirect(url_for('auth.login'))
            
        if not user.check_password(form.password.data):
            user.increment_failed_attempts()
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
            
        user.reset_failed_attempts()
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    from flask_login import current_user
    from app.models import User
    from app.email import send_verification_email
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.is_verified = False
        user.save()
        
        from app.models import Activity
        Activity.record(user.id, 'registration', 'Joined the community!')
        
        send_verification_email(user)
        flash('Congratulations, you are now a registered user! Please check your email to verify your account.')
        return redirect(url_for('auth.login'))
    elif request.method == 'POST':
        print(f"DEBUG: Form errors: {form.errors}")
    return render_template('auth/signup.html', title='Register', form=form)

@bp.route('/verify/<token>')
def verify_email(token):
    from app.models import User
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_token(token, salt='email-verify')
    if user:
        if user.is_verified:
            flash('Account already verified.')
        else:
            user.is_verified = True
            user.save()
            flash('Your account has been verified!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('auth.login'))

@bp.route('/notifications/mark_read', methods=['POST'])
@login_required
def mark_notifications_read():
    from app.models import Notification
    from flask import jsonify
    Notification.mark_all_read(current_user.id)
    return jsonify({'status': 'success'})

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    from app.auth.forms import PasswordResetRequestForm
    from app.models import User
    from app.email import send_password_reset_email
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from app.auth.forms import ResetPasswordForm
    from app.models import User
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_token(token, salt='password-reset')
    if not user:
        flash('The reset link is invalid or has expired.')
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='Profile')

@bp.route('/user/<username>')
def public_profile(username):
    from app.models import User, Soundboard
    user = User.get_by_username(username)
    if not user:
        flash('User not found.')
        return redirect(url_for('main.index'))
    
    public_sbs = Soundboard.get_by_user_id(user.id)
    # Filter for public only if it's not the owner viewing their own public profile 
    # (actually public profile should always show only public sbs)
    public_sbs = [sb for sb in public_sbs if sb.is_public]
    
    return render_template('auth/public_profile.html', title=f'{user.username}\'s Profile', user=user, soundboards=public_sbs)

@bp.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    from app.auth.forms import UpdateProfileForm
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        current_user.social_x = form.social_x.data
        current_user.social_youtube = form.social_youtube.data
        current_user.social_website = form.social_website.data
        
        if form.avatar.data:
            f = form.avatar.data
            filename = secure_filename(f"{current_user.id}_{f.filename}")
            avatar_path = os.path.join('avatars', filename)
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], avatar_path)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            f.save(full_path)
            current_user.avatar_path = avatar_path
            
        current_user.save()
        flash('Your profile has been updated.')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.social_x.data = current_user.social_x
        form.social_youtube.data = current_user.social_youtube
        form.social_website.data = current_user.social_website
    return render_template('auth/update_profile.html', title='Update Profile', form=form)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    from app.auth.forms import ChangePasswordForm
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Invalid current password.')
            return redirect(url_for('auth.change_password'))
        current_user.set_password(form.password.data)
        current_user.save()
        flash('Your password has been updated.')
        return redirect(url_for('auth.profile'))
    return render_template('auth/change_password.html', title='Change Password', form=form)

@bp.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    from app.auth.forms import DeleteAccountForm
    from flask_login import logout_user
    form = DeleteAccountForm()
    if form.validate_on_submit():
        user = current_user
        logout_user()
        user.delete()
        flash('Your account and all associated data have been permanently deleted.')
        return redirect(url_for('main.index'))
    return render_template('auth/delete_account.html', title='Delete Account', form=form)
