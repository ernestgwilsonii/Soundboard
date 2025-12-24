import pytest
from app import create_app
import os
import sqlite3
from config import Config
from app.models import User

@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath('test_accounts_admin.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_admin.sqlite3')
    
    monkeypatch.setattr(Config, 'ACCOUNTS_DB', accounts_db)
    monkeypatch.setattr(Config, 'SOUNDBOARDS_DB', soundboards_db)
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)
        
    with app.app_context():
        with sqlite3.connect(accounts_db) as conn:
            with open('app/schema_accounts.sql', 'r') as f:
                conn.executescript(f.read())
        with sqlite3.connect(soundboards_db) as conn:
            with open('app/schema_soundboards.sql', 'r') as f:
                conn.executescript(f.read())
                
    with app.test_client() as client:
        yield client
        
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_admin_settings_access_denied_for_user(client):
    # Create a regular user
    with client.application.app_context():
        u = User(username='regularuser', email='user@example.com', role='user')
        u.set_password('password')
        u.save()
    
    client.post('/auth/login', data={'username': 'regularuser', 'password': 'password', 'submit': 'Sign In'})
    response = client.get('/admin/settings', follow_redirects=True)
    # Depending on how admin_required is implemented, it might redirect to index with a flash message
    assert response.status_code == 200
    assert b"You do not have permission" in response.data or response.request.path == '/'

def test_admin_settings_access_allowed_for_admin(client):
    # Create an admin user
    with client.application.app_context():
        u = User(username='adminuser', email='admin@example.com', role='admin')
        u.set_password('password')
        u.save()
    
    client.post('/auth/login', data={'username': 'adminuser', 'password': 'password', 'submit': 'Sign In'})
    response = client.get('/admin/settings')
    assert response.status_code == 200
    assert b"Admin Settings" in response.data

def test_update_featured_soundboard(client):
    # Create an admin user
    with client.application.app_context():
        u = User(username='adminuser2', email='admin2@example.com', role='admin')
        u.set_password('password')
        u.save()
    
    client.post('/auth/login', data={'username': 'adminuser2', 'password': 'password', 'submit': 'Sign In'})
    
    # Post to update featured soundboard
    response = client.post('/admin/settings', data={
        'featured_soundboard_id': '5',
        'submit': 'Save Settings'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Settings updated" in response.data
    
    # Verify in DB
    with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM admin_settings WHERE key = 'featured_soundboard_id'")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == '5'
