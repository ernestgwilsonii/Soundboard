import pytest
from app import create_app
from app.auth.forms import RegistrationForm, LoginForm

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

def test_registration_form(app):
    with app.app_context():
        form = RegistrationForm(username='test', email='test@example.com', 
                                password='cat', password_confirm='cat')
        assert form.validate()

def test_registration_form_password_mismatch(app):
    with app.app_context():
        form = RegistrationForm(username='test', email='test@example.com', 
                                password='cat', password_confirm='dog')
        assert not form.validate()
        assert 'Passwords must match' in form.password_confirm.errors

def test_login_form(app):
    with app.app_context():
        form = LoginForm(username='test', password='cat')
        assert form.validate()

def test_soundboard_form(app):
    from app.soundboard.forms import SoundboardForm
    with app.app_context():
        # Valid form
        form = SoundboardForm(name='New Board', icon='fas fa-music')
        assert form.validate()
        
        # Invalid form (missing name)
        form = SoundboardForm(name='', icon='fas fa-music')
        assert not form.validate()
