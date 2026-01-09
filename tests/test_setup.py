import os


def test_requirements_file_exists():
    assert os.path.exists("requirements.txt")


def test_requirements_content():
    with open("requirements.txt", "r") as f:
        content = f.read()
        assert "Flask" in content
        assert "Flask-WTF" in content
        assert "python-dotenv" in content
        assert "Werkzeug" in content


def test_directory_structure():
    assert os.path.exists("app")
    assert os.path.exists("static")
    assert os.path.exists("templates")
    assert os.path.isdir("app")
    assert os.path.isdir("static")
    assert os.path.isdir("templates")


def test_env_example_exists():
    assert os.path.exists(".env.example")


def test_env_example_content():
    with open(".env.example", "r") as f:
        content = f.read()
        assert "SECRET_KEY" in content
        assert "DEBUG" in content


def test_config_loading():
    # This will fail until config.py is created
    from dotenv import load_dotenv

    import config

    load_dotenv()

    assert hasattr(config, "Config")
    assert hasattr(config.Config, "SECRET_KEY")
    assert hasattr(config.Config, "DEBUG")
    assert config.Config.SECRET_KEY is not None


def test_app_factory():
    from flask import Flask

    from app import create_app

    app = create_app()
    assert isinstance(app, Flask)
    assert app.config["SECRET_KEY"] is not None


def test_logging_configuration():
    from app import create_app
    from config import Config

    class TestConfig(Config):
        DEBUG = False
        TESTING = False  # Logging is disabled when TESTING is True in our create_app

    app = create_app(config_class=TestConfig)
    # Check if a file handler is added for production (not DEBUG)
    assert len(app.logger.handlers) > 0


def test_login_manager_initialized():
    from app import create_app

    app = create_app()
    assert hasattr(app, "login_manager")


def test_upload_config():
    from app import create_app

    app = create_app()
    assert "UPLOAD_FOLDER" in app.config
    assert app.config["MAX_CONTENT_LENGTH"] == 5 * 1024 * 1024
    assert "mp3" in app.config["ALLOWED_EXTENSIONS"]
