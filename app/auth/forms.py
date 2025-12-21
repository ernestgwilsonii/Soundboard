from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlite3
from config import Config

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3)])
    password_confirm = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (username.data,))
            if cur.fetchone():
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = ?", (email.data,))
            if cur.fetchone():
                raise ValidationError('Please use a different email address.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
