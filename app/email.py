from flask_mail import Message
from app import mail
from flask import render_template, current_app
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # Use threading for async sending to avoid blocking
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_verification_email(user):
    token = user.get_token(salt='email-verify')
    send_email(
        '[Soundboard] Verify Your Account',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/verify_account.txt', user=user, token=token),
        html_body=render_template('email/verify_account.html', user=user, token=token)
    )

def send_password_reset_email(user):
    token = user.get_token(salt='password-reset')
    send_email(
        '[Soundboard] Reset Your Password',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )
