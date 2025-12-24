from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField, SelectField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError
import sqlite3
from config import Config

class AdminPasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=3)])
    password_confirm = PasswordField(
        'Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

class AdminUpdateEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Update Email')

    def __init__(self, user_id, *args, **kwargs):
        super(AdminUpdateEmailForm, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_email(self, email):
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email.data, self.user_id))
            if cur.fetchone():
                raise ValidationError('This email is already in use by another account.')

class PlatformSettingsForm(FlaskForm):
    featured_soundboard_id = StringField('Featured Soundboard ID')
    
    announcement_message = StringField('Announcement Banner Message')
    announcement_type = SelectField('Banner Type', choices=[
        ('info', 'Info (Blue)'),
        ('warning', 'Warning (Yellow)'),
        ('danger', 'Critical (Red)'),
        ('success', 'Success (Green)')
    ], default='info')
    
    maintenance_mode = BooleanField('Enable Maintenance Mode')
    
    submit = SubmitField('Save Settings')
