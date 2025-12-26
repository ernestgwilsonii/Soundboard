import pytest
import os
import sqlite3
from app import create_app
from app.models import User
from config import Config

@pytest.fixture
def client(monkeypatch):
    # Use temporary DBs
    accounts_db = os.path.abspath('test_accounts_follows.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_follows.sqlite3')
    
    monkeypatch.setattr(Config, 'ACCOUNTS_DB', accounts_db)
    monkeypatch.setattr(Config, 'SOUNDBOARDS_DB', soundboards_db)
    
    app = create_app()
    app.config['TESTING'] = True
    
    # Initialize DBs
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)
        
    with app.app_context():
        with sqlite3.connect(accounts_db) as conn:
            with open('app/schema_accounts.sql', 'r') as f:
                conn.executescript(f.read())
            # Also apply migration manually for test
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
        
    # Cleanup
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_user_follow_unfollow(client):
    with client.application.app_context():
        u1 = User(username='user1', email='u1@test.com')
        u1.set_password('pass1')
        u1.save()
        u2 = User(username='user2', email='u2@test.com')
        u2.set_password('pass2')
        u2.save()
        
        # Test follow
        u1.follow(u2.id)
        assert u1.is_following(u2.id) is True
        assert u2.get_follower_count() == 1
        assert u1.get_following_count() == 1
        
        # Test following list
        following = u1.get_following()
        assert len(following) == 1
        assert following[0].id == u2.id
        
        # Test followers list
        followers = u2.get_followers()
        assert len(followers) == 1
        assert followers[0].id == u1.id
        
        # Test unfollow
        u1.unfollow(u2.id)
        assert u1.is_following(u2.id) is False
        assert u2.get_follower_count() == 0
        assert u1.get_following_count() == 0
