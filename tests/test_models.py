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

def test_user_mixin_inheritance(app):
    from flask_login import UserMixin
    u = User(username='test', email='test@example.com')
    assert isinstance(u, UserMixin)
    assert u.is_authenticated
    assert u.is_active is True
    assert not u.is_anonymous

def test_user_active_status(app):
    u = User(username='inactive', email='inactive@e.com', active=False)
    u.set_password('cat')
    u.save()
    
    u2 = User.get_by_id(u.id)
    assert u2.active is False
    assert u2.is_active is False

def test_user_favorites(app):
    u = User(username='favuser', email='fav@e.com')
    u.set_password('cat')
    u.save()
    
    # Add favorite
    u.add_favorite(101)
    favorites = u.get_favorites()
    assert 101 in favorites
    
    # Remove favorite
    u.remove_favorite(101)
    favorites = u.get_favorites()
    assert 101 not in favorites

def test_user_get_all(app):
    # Already some users created in previous tests might exist if not cleared
    # But fixture clears them.
    u1 = User(username='user1', email='u1@e.com')
    u1.set_password('cat')
    u1.save()
    u2 = User(username='user2', email='u2@e.com')
    u2.set_password('cat')
    u2.save()
    
    users = User.get_all()
    assert len(users) >= 2
    usernames = [u.username for u in users]
    assert 'user1' in usernames
    assert 'user2' in usernames

def test_soundboard_model(app):
    s = Soundboard(name='My Board', user_id=1, icon='fas fa-music', is_public=True)
    assert s.name == 'My Board'
    assert s.user_id == 1
    assert s.icon == 'fas fa-music'
    assert s.is_public is True
    assert str(s) == '<Soundboard My Board>'

def test_soundboard_get_all(app):
    s1 = Soundboard(name='SB1', user_id=1)
    s1.save()
    s2 = Soundboard(name='SB2', user_id=1)
    s2.save()
    
    sbs = Soundboard.get_all()
    assert len(sbs) >= 2
    names = [s.name for s in sbs]
    assert 'SB1' in names
    assert 'SB2' in names

def test_sound_model(app):
    s = Sound(name='Explosion', soundboard_id=1, file_path='sounds/1/explosion.mp3', icon='fas fa-bomb')
    assert s.name == 'Explosion'
    assert s.soundboard_id == 1
    assert s.file_path == 'sounds/1/explosion.mp3'
    assert s.icon == 'fas fa-bomb'
    assert str(s) == '<Sound Explosion>'

def test_soundboard_crud(app):
    # Create
    s = Soundboard(name='CRUD Board', user_id=1, icon='test-icon', is_public=True)
    s.save()
    assert s.id is not None
    
    # Read
    s2 = Soundboard.get_by_id(s.id)
    assert s2.name == 'CRUD Board'
    assert s2.is_public is True
    
    # Update
    s2.is_public = False
    s2.save()
    s3 = Soundboard.get_by_id(s.id)
    assert s3.is_public is False
    
    # Delete
    s3.delete()
    assert Soundboard.get_by_id(s.id) is None

def test_soundboard_get_public(app):
    # Create public and private boards
    s1 = Soundboard(name='Public Board', user_id=1, is_public=True)
    s1.save()
    s2 = Soundboard(name='Private Board', user_id=1, is_public=False)
    s2.save()
    
    public_boards = Soundboard.get_public()
    assert len(public_boards) >= 1
    assert any(b.name == 'Public Board' for b in public_boards)
    assert all(b.is_public for b in public_boards)
    assert not any(b.name == 'Private Board' for b in public_boards)

def test_soundboard_search(app):
    from app.models import User, Soundboard, Sound
    with app.app_context():
        u = User(username='searcher', email='search@example.com')
        u.set_password('cat')
        u.save()
        
        # Board with specific name
        s1 = Soundboard(name='Unique Name Board', user_id=u.id, is_public=True)
        s1.save()
        
        # Board with specific sound
        s2 = Soundboard(name='Sound Host', user_id=u.id, is_public=True)
        s2.save()
        snd = Sound(name='Target Sound', soundboard_id=s2.id, file_path='p')
        snd.save()
        
        # Private board (should not be found)
        s3 = Soundboard(name='Private Target', user_id=u.id, is_public=False)
        s3.save()
        
        # Search by board name
        results = Soundboard.search('Unique')
        assert any(b.name == 'Unique Name Board' for b in results)
        
        # Search by username
        results = Soundboard.search('searcher')
        assert len(results) >= 2
        
        # Search by sound name
        results = Soundboard.search('Target')
        assert any(b.name == 'Sound Host' for b in results)
        assert not any(b.name == 'Private Target' for b in results)

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