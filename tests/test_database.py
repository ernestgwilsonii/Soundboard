import sqlite3
import os
import pytest
from config import Config

def test_accounts_schema():
    # Use an in-memory database for testing schema
    db = sqlite3.connect(':memory:')
    with open('app/schema_accounts.sql', 'r') as f:
        db.executescript(f.read())
    
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    assert cursor.fetchone() is not None
    
    cursor.execute("PRAGMA table_info(users);")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'id' in columns
    assert 'username' in columns
    assert 'email' in columns
    assert 'password_hash' in columns
    assert 'role' in columns

def test_soundboards_schema():
    db = sqlite3.connect(':memory:')
    with open('app/schema_soundboards.sql', 'r') as f:
        db.executescript(f.read())
    
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='soundboards';")
    assert cursor.fetchone() is not None
    
    cursor.execute("PRAGMA table_info(soundboards);")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'id' in columns
    assert 'name' in columns
    assert 'user_id' in columns
    assert 'icon' in columns

def test_init_db():
    from init_db import init_db
    # Use temporary database paths for testing
    test_accounts_db = 'test_accounts.sqlite3'
    test_soundboards_db = 'test_soundboards.sqlite3'
    
    # Ensure they don't exist
    if os.path.exists(test_accounts_db): os.remove(test_accounts_db)
    if os.path.exists(test_soundboards_db): os.remove(test_soundboards_db)
    
    init_db(test_accounts_db, test_soundboards_db)
    
    assert os.path.exists(test_accounts_db)
    assert os.path.exists(test_soundboards_db)
    
    # Cleanup
    os.remove(test_accounts_db)
    os.remove(test_soundboards_db)

def test_load_user():
    from app import login
    # This might need mock or real DB setup
    from app.models import User
    import sqlite3
    
    # Create a temporary DB with a user
    db_path = 'test_load_user.sqlite3'
    if os.path.exists(db_path): os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
        with open('app/schema_accounts.sql', 'r') as f:
            conn.executescript(f.read())
        conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                     ('loader', 'loader@example.com', 'hash'))
    
    # Monkeypatch Config.ACCOUNTS_DB or provide a way to use this test DB
    import app
    original_db = app.Config.ACCOUNTS_DB
    app.Config.ACCOUNTS_DB = os.path.abspath(db_path)
    
    user = app.login._user_callback(1)
    assert user is not None
    assert user.username == 'loader'
    
    # Cleanup
    app.Config.ACCOUNTS_DB = original_db
    os.remove(db_path)
