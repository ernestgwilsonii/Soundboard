import pytest
import os
import sqlite3
from app import create_app
from app.models import User
from config import Config

@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath('test_accounts_follow_routes.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_follow_routes.sqlite3')
    
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
        with sqlite3.connect(soundboards_db) as conn:
            with open('app/schema_soundboards.sql', 'r') as f:
                conn.executescript(f.read())
                
    with app.test_client() as client:
        yield client
        
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_follow_unfollow_routes(client):
    with client.application.app_context():
        u1 = User(username='follower', email='f@test.com', is_verified=True)
        u1.set_password('pass')
        u1.save()
        u2 = User(username='followed', email='d@test.com', is_verified=True)
        u2.set_password('pass')
        u2.save()
        
    # Login
    client.post('/auth/login', data={'username': 'follower', 'password': 'pass'})
    
    # Follow
    response = client.post('/auth/follow/followed', follow_redirects=True)
    assert response.status_code == 200
    assert b'You are now following followed' in response.data
    
    with client.application.app_context():
        u1_obj = User.get_by_username('follower')
        u2_obj = User.get_by_username('followed')
        assert u1_obj.is_following(u2_obj.id) is True
        
    # Unfollow
    response = client.post('/auth/unfollow/followed', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have unfollowed followed' in response.data
    
    with client.application.app_context():
        u1_obj = User.get_by_username('follower')
        u2_obj = User.get_by_username('followed')
        assert u1_obj.is_following(u2_obj.id) is False

def test_follow_self_fails(client):
    with client.application.app_context():
        u1 = User(username='self', email='s@test.com', is_verified=True)
        u1.set_password('pass')
        u1.save()
        
    client.post('/auth/login', data={'username': 'self', 'password': 'pass'})
    
    response = client.post('/auth/follow/self', follow_redirects=True)
    assert b'You cannot follow yourself' in response.data

def test_follow_button_rendering(client):
    with client.application.app_context():
        u1 = User(username='user1', email='u1@test.com', is_verified=True)
        u1.set_password('pass')
        u1.save()
        u2 = User(username='user2', email='u2@test.com', is_verified=True)
        u2.set_password('pass')
        u2.save()
        
    # Not logged in - no button
    response = client.get('/auth/user/user2')
    assert b'btn-primary px-4">Follow</button>' not in response.data
    
    # Logged in as user1
    client.post('/auth/login', data={'username': 'user1', 'password': 'pass'})
    response = client.get('/auth/user/user2')
    assert b'btn-primary px-4">Follow</button>' in response.data
    
    # Follow user2
    client.post('/auth/follow/user2')
    response = client.get('/auth/user/user2')
    assert b'btn-outline-danger px-4">Unfollow</button>' in response.data

def test_members_list_route(client):
    with client.application.app_context():
        u1 = User(username='member1', email='m1@test.com', is_verified=True)
        u1.set_password('pass')
        u1.save()
        u2 = User(username='member2', email='m2@test.com', is_verified=True)
        u2.set_password('pass')
        u2.save()
        
    # Unauthenticated
    response = client.get('/auth/members', follow_redirects=True)
    assert b'Sign In' in response.data
    
    # Authenticated
    client.post('/auth/login', data={'username': 'member1', 'password': 'pass'})
    response = client.get('/auth/members')
    assert response.status_code == 200
    assert b'member1' in response.data
    assert b'member2' in response.data

def test_follower_following_lists(client):
    with client.application.app_context():
        u1 = User(username='user_a', email='a@test.com', is_verified=True)
        u1.set_password('pass')
        u1.save()
        u2 = User(username='user_b', email='b@test.com', is_verified=True)
        u2.set_password('pass')
        u2.save()
        u1.follow(u2.id)
        
    client.post('/auth/login', data={'username': 'user_a', 'password': 'pass'})
    
    # Check following list for user_a
    response = client.get('/auth/user/user_a/following')
    assert response.status_code == 200
    assert b'user_b' in response.data
    
    # Check followers list for user_b
    response = client.get('/auth/user/user_b/followers')
    assert response.status_code == 200
    assert b'user_a' in response.data
