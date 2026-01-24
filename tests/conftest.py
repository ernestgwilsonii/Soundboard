import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import uuid

import pytest

from app import create_app
from app.extensions import db_orm
from config import Config


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="session")
def live_server_url():
    """Starts the Flask server in a subprocess and yields the base URL."""
    port = get_open_port()
    url = f"http://127.0.0.1:{port}"

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Use a dedicated test DB for automation to avoid side effects
    test_accounts_db = os.path.abspath("test_automation_accounts.sqlite3")
    test_soundboards_db = os.path.abspath("test_automation_soundboards.sqlite3")
    temp_upload_folder = tempfile.mkdtemp()

    # Environment variables for the test server
    env = os.environ.copy()
    env["FLASK_RUN_PORT"] = str(port)
    env["ACCOUNTS_DB"] = test_accounts_db
    env["SOUNDBOARDS_DB"] = test_soundboards_db
    env["TESTING"] = "True"
    env["DEBUG"] = "False"
    env["WTF_CSRF_ENABLED"] = "False"  # Simplify E2E forms
    env["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{test_accounts_db}"
    env["SQLALCHEMY_BINDS_SOUNDBOARDS"] = f"sqlite:///{test_soundboards_db}"
    env["UPLOAD_FOLDER"] = temp_upload_folder

    print(f"\n[Harness] Starting server on {url}...")

    # Start server and pipe logs
    import sys

    python_exe = sys.executable
    with open("logs/test_server.log", "w") as log_file:
        proc = subprocess.Popen(
            [python_exe, "soundboard.py"],
            env=env,
            stdout=log_file,
            stderr=log_file,
            preexec_fn=os.setsid,  # Create process group for clean kill
        )

        # Poll for availability
        start_time = time.time()
        timeout = 60
        connected = False
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    print("[Harness] Server is UP!")
                    connected = True
                    break
            except Exception:
                time.sleep(1)

        if not connected:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            # Try to read logs for error
            with open("logs/test_server.log", "r") as f:
                log_tail = f.read()
            raise Exception(f"Timeout: Test server failed to start. Logs:\n{log_tail}")

        yield url

        print("[Harness] Stopping server...")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        if os.path.exists(temp_upload_folder):
            shutil.rmtree(temp_upload_folder)


@pytest.fixture(scope="function")
def test_db_setup():
    """Ensures fresh databases are initialized before each test for E2E."""
    test_accounts_db = os.path.abspath("test_automation_accounts.sqlite3")
    test_soundboards_db = os.path.abspath("test_automation_soundboards.sqlite3")

    # We don't change UPLOAD_FOLDER here because the server is already running with one.
    # But we might want to clear it?

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{test_accounts_db}"
        SQLALCHEMY_BINDS = {"soundboards": f"sqlite:///{test_soundboards_db}"}
        WTF_CSRF_ENABLED = False

    app = create_app(TestConfig)

    with app.app_context():
        from app.models import (  # noqa: F401
            Activity,
            AdminSettings,
            BoardCollaborator,
            Comment,
            Notification,
            Playlist,
            PlaylistItem,
            Rating,
            Sound,
            Soundboard,
            SoundboardTag,
            User,
        )

        print(f"DEBUG: Registered tables: {list(db_orm.metadata.tables.keys())}")
        db_orm.drop_all()
        db_orm.create_all()
        AdminSettings.set_setting("featured_soundboard_id", None)

        yield test_accounts_db, test_soundboards_db

        db_orm.session.remove()
        # No drop_all here because we want the files to stay for the server to see them
        # but we remove them at the start of next test anyway.

    # Note: We don't remove files here because the server might still be using them
    # between yield and next test setup.


@pytest.fixture
def app():
    """App fixture for unit and integration tests."""
    suffix = uuid.uuid4().hex[:8]
    test_accounts_db = os.path.abspath(f"test_app_accounts_{suffix}.sqlite3")
    test_soundboards_db = os.path.abspath(f"test_app_soundboards_{suffix}.sqlite3")
    temp_upload_folder = tempfile.mkdtemp()

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{test_accounts_db}"
        SQLALCHEMY_BINDS = {"soundboards": f"sqlite:///{test_soundboards_db}"}
        WTF_CSRF_ENABLED = False
        UPLOAD_FOLDER = temp_upload_folder
        SECRET_KEY = "test-secret-key"

    app = create_app(TestConfig)

    with app.app_context():
        from app.models import (  # noqa: F401
            Activity,
            AdminSettings,
            BoardCollaborator,
            Comment,
            Notification,
            Playlist,
            PlaylistItem,
            Rating,
            Sound,
            Soundboard,
            SoundboardTag,
            User,
        )

        print(f"DEBUG: Registered tables: {list(db_orm.metadata.tables.keys())}")
        db_orm.create_all()
        AdminSettings.set_setting("featured_soundboard_id", None)

        yield app

        db_orm.session.remove()
        db_orm.drop_all()

    for db_path in [test_accounts_db, test_soundboards_db]:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
    if os.path.exists(temp_upload_folder):
        shutil.rmtree(temp_upload_folder)


@pytest.fixture
def client(app):
    """Client fixture for unit and integration tests."""
    return app.test_client()
