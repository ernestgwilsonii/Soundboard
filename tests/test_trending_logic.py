import pytest
import os
import sqlite3
from app import create_app
from app.models import User, Soundboard, Rating
from config import Config

@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath('test_accounts_trending.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_trending.sqlite3')
    monkeypatch.setattr(Config, 'ACCOUNTS_DB', accounts_db)
    monkeypatch.setattr(Config, 'SOUNDBOARDS_DB', soundboards_db)
    app = create_app()
    app.config['TESTING'] = True
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)
    with app.app_context():
        with sqlite3.connect(accounts_db) as conn:
            with open('app/schema_accounts.sql', 'r') as f: conn.executescript(f.read())
        with sqlite3.connect(soundboards_db) as conn:
            with open('app/schema_soundboards.sql', 'r') as f: conn.executescript(f.read())
    with app.test_client() as client:
        yield client
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_get_trending_logic(client):
    with client.application.app_context():
        # Setup users
        u1 = User(username='u1', email='u1@t.com'); u1.set_password('p'); u1.save()
        u2 = User(username='u2', email='u2@t.com'); u2.set_password('p'); u2.save()
        
        # u2 follows u1 (u1 has 1 follower)
        u2.follow(u1.id)
        
        # Setup boards
        # sb1: high rating, 1 creator follower
        sb1 = Soundboard(name='High Rated', user_id=u1.id, is_public=True); sb1.save()
        Rating(user_id=u2.id, soundboard_id=sb1.id, score=5).save()
        
        # sb2: low rating, 0 creator followers
        sb2 = Soundboard(name='Low Rated', user_id=u2.id, is_public=True); sb2.save()
        Rating(user_id=u1.id, soundboard_id=sb2.id, score=1).save()
        
        trending = Soundboard.get_trending()
        
        assert trending[0].id == sb1.id
        assert trending[1].id == sb2.id
        assert len(trending) == 2
