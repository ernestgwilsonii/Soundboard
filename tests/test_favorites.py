import pytest
from app import create_app
import os
import sqlite3
from config import Config
from app.models import User, Soundboard

@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath('test_accounts_favs.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_favs.sqlite3')
    
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

def test_toggle_favorite_endpoint(client):
    # Setup
    with client.application.app_context():
        u = User(username='favuser', email='fav@example.com')
        u.set_password('pass')
        u.save()
        sb = Soundboard(name='Fav Board', user_id=u.id, is_public=True)
        sb.save()
        sb_id = sb.id
        
    # Login
    client.post('/auth/login', data={'username': 'favuser', 'password': 'pass', 'submit': 'Sign In'})
    
    # Toggle ON
    response = client.post(f'/soundboard/{sb_id}/favorite', follow_redirects=True)
    assert response.status_code == 200
    assert response.get_json()['is_favorite'] == True
    
    # Verify DB
    with client.application.app_context():
        u = User.get_by_username('favuser')
        assert sb_id in u.get_favorites()
        
    # Toggle OFF
    response = client.post(f'/soundboard/{sb_id}/favorite', follow_redirects=True)
    assert response.status_code == 200
    assert response.get_json()['is_favorite'] == False
    
    # Verify DB
    with client.application.app_context():
        u = User.get_by_username('favuser')
        assert sb_id not in u.get_favorites()

def test_favorite_status_in_view(client):
    # Setup
    with client.application.app_context():
        u = User(username='viewuser', email='view@example.com')
        u.set_password('pass')
        u.save()
        sb = Soundboard(name='Fav View Board', user_id=u.id, is_public=True)
        sb.save()
        sb_id = sb.id
        u.add_favorite(sb_id)
        
    client.post('/auth/login', data={'username': 'viewuser', 'password': 'pass', 'submit': 'Sign In'})
    
    response = client.get(f'/soundboard/view/{sb_id}')
    assert b'is_favorite = true' in response.data.lower() or b'favorite-btn active' in response.data.lower() or b'text-warning' in response.data.lower()
