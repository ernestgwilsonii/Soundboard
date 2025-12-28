import pytest
import subprocess
import os
import signal
import time
import socket
import sqlite3
import shutil
from config import Config

def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

@pytest.fixture(scope="session")
def live_server_url():
    """Starts the Flask server in a subprocess and yields the base URL."""
    port = get_open_port()
    url = f"http://127.0.0.1:{port}"
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Use a dedicated test DB for automation to avoid side effects
    test_accounts_db = os.path.abspath('test_automation_accounts.sqlite3')
    test_soundboards_db = os.path.abspath('test_automation_soundboards.sqlite3')
    
    # Environment variables for the test server
    env = os.environ.copy()
    env["FLASK_RUN_PORT"] = str(port)
    env["ACCOUNTS_DB"] = test_accounts_db
    env["SOUNDBOARDS_DB"] = test_soundboards_db
    env["TESTING"] = "True"
    env["WTF_CSRF_ENABLED"] = "False" # Simplify E2E forms
    
    print(f"\n[Harness] Starting server on {url}...")
    
    # Start server and pipe logs
    with open('logs/test_server.log', 'w') as log_file:
        proc = subprocess.Popen(
            ["venv/bin/python", "soundboard.py"],
            env=env,
            stdout=log_file,
            stderr=log_file,
            preexec_fn=os.setsid # Create process group for clean kill
        )
        
        # Poll for availability
        start_time = time.time()
        timeout = 15
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    print("[Harness] Server is UP!")
                    break
            except:
                time.sleep(0.5)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            raise Exception("Timeout: Test server failed to start.")
            
        yield url
        
        print("[Harness] Stopping server...")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

@pytest.fixture(scope="function")
def test_db_setup(monkeypatch):
    """Ensures fresh databases are initialized before each test."""
    test_accounts_db = os.path.abspath('test_automation_accounts.sqlite3')
    test_soundboards_db = os.path.abspath('test_automation_soundboards.sqlite3')
    
    # Clean old files
    for db in [test_accounts_db, test_soundboards_db]:
        if os.path.exists(db):
            os.remove(db)
            
    # Initialize schemas
    with sqlite3.connect(test_accounts_db) as conn:
        with open('app/schema_accounts.sql', 'r') as f:
            conn.executescript(f.read())
        # Manual migration for follows
        conn.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER NOT NULL,
                followed_id INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, followed_id),
                FOREIGN KEY (follower_id) REFERENCES users (id),
                FOREIGN KEY (followed_id) REFERENCES users (id)
            );
        """)
            
    with sqlite3.connect(test_soundboards_db) as conn:
        with open('app/schema_soundboards.sql', 'r') as f:
            conn.executescript(f.read())
        # Manual migrations for soundboards
        conn.execute("ALTER TABLE soundboards ADD COLUMN theme_preset TEXT DEFAULT 'default'")
        conn.execute("ALTER TABLE sounds ADD COLUMN bitrate INTEGER")
        conn.execute("ALTER TABLE sounds ADD COLUMN file_size INTEGER")
        conn.execute("ALTER TABLE sounds ADD COLUMN format TEXT")
            
    return test_accounts_db, test_soundboards_db
