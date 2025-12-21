import pytest
import os
import sqlite3
from app import create_app
from app.models import User, Soundboard, Sound
from config import Config

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    # Use in-memory or temp DBs for tests? 
    # For models, let's use temp files to avoid clobbering dev DBs
    app.config['ACCOUNTS_DB'] = 'test_accounts_models.sqlite3'
    app.config['SOUNDBOARDS_DB'] = 'test_soundboards_models.sqlite3'
    
    with app.app_context():
        # Initialize test DBs
        for db_path in [app.config['ACCOUNTS_DB'], app.config['SOUNDBOARDS_DB']]:
            if os.path.exists(db_path): os.remove(db_path)
            
        with sqlite3.connect(app.config['ACCOUNTS_DB']) as conn:
            with open('app/schema_accounts.sql', 'r') as f:
                conn.executescript(f.read())
        with sqlite3.connect(app.config['SOUNDBOARDS_DB']) as conn:
            with open('app/schema_soundboards.sql', 'r') as f:
                conn.executescript(f.read())
                
        yield app
        
        # Cleanup
        for db_path in [app.config['ACCOUNTS_DB'], app.config['SOUNDBOARDS_DB']]:
            if os.path.exists(db_path): os.remove(db_path)

def test_user_password_hashing(app):
    u = User(username='test', email='test@example.com')
    u.set_password('cat')
    assert not u.check_password('dog')
    assert u.check_password('cat')

def test_user_representation(app):
    u = User(username='test', email='test@example.com')
    assert str(u) == '<User test>'

def test_soundboard_model(app):
    s = Soundboard(name='My Board', user_id=1, icon='fas fa-music')
    assert s.name == 'My Board'
    assert s.user_id == 1
    assert s.icon == 'fas fa-music'
    assert str(s) == '<Soundboard My Board>'

def test_sound_model(app):
    s = Sound(name='Explosion', soundboard_id=1, file_path='sounds/1/explosion.mp3', icon='fas fa-bomb')
    assert s.name == 'Explosion'
    assert s.soundboard_id == 1
    assert s.file_path == 'sounds/1/explosion.mp3'
    assert s.icon == 'fas fa-bomb'
    assert str(s) == '<Sound Explosion>'

def test_soundboard_crud(app):
    # Create
    s = Soundboard(name='CRUD Board', user_id=1, icon='test-icon')
    s.save()
    assert s.id is not None
    
    # Read
    s2 = Soundboard.get_by_id(s.id)
    assert s2.name == 'CRUD Board'
    
    # Update
    s2.name = 'Updated Board'
    s2.save()
    s3 = Soundboard.get_by_id(s.id)
    assert s3.name == 'Updated Board'
    
    # Delete
    s3.delete()
    assert Soundboard.get_by_id(s.id) is None

def test_sound_crud(app):
    # Create
    s = Sound(name='CRUD Sound', soundboard_id=1, file_path='path/to/file', icon='test-icon')
    s.save()
    assert s.id is not None
    
    # Read
    s2 = Sound.get_by_id(s.id)
    assert s2.name == 'CRUD Sound'
    
    # Update
    s2.name = 'Updated Sound'
    s2.save()
    s3 = Sound.get_by_id(s.id)
    assert s3.name == 'Updated Sound'
    
    # Delete
    s3.delete()
    assert Sound.get_by_id(s.id) is None