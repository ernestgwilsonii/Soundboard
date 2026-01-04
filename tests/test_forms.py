import pytest

from app import create_app
from app.auth.forms import LoginForm, RegistrationForm


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def test_registration_form(app):
    with app.app_context():
        form = RegistrationForm(
            username="test",
            email="test@example.com",
            password="cat",
            password_confirm="cat",
        )
        assert form.validate()


def test_registration_form_password_mismatch(app):
    with app.app_context():
        form = RegistrationForm(
            username="test",
            email="test@example.com",
            password="cat",
            password_confirm="dog",
        )
        assert not form.validate()
        assert "Passwords must match" in form.password_confirm.errors


def test_login_form(app):
    with app.app_context():
        form = LoginForm(username="test", password="cat")
        assert form.validate()


def test_soundboard_form(app):
    from app.soundboard.forms import SoundboardForm

    with app.app_context():
        # Valid form
        form = SoundboardForm(name="New Board", icon="fas fa-music", is_public=True)
        assert form.validate()
        assert form.is_public.data is True

        # Invalid form (missing name)
        form = SoundboardForm(name="", icon="fas fa-music")
        assert not form.validate()


def test_admin_password_reset_form(app):
    from app.admin.forms import AdminPasswordResetForm

    with app.app_context():
        # Valid
        form = AdminPasswordResetForm(password="newpass", password_confirm="newpass")
        assert form.validate()

        # Mismatch
        form = AdminPasswordResetForm(password="newpass", password_confirm="wrong")
        assert not form.validate()


def test_sound_form(app):
    from app.soundboard.forms import SoundForm

    with app.app_context():
        # Note: Testing file fields usually requires mock file objects
        form = SoundForm(name="Explosion", icon="fas fa-bomb")
        # We don't provide a file here, so it might fail depending on if it's required
        assert not form.validate()  # Should fail because file is required
