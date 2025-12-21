import pytest
from app.models import User, Soundboard, Sound
from flask_login import UserMixin

def test_user_password_hashing():
    u = User(username='test', email='test@example.com')
    u.set_password('cat')
    assert not u.check_password('dog')
    assert u.check_password('cat')

def test_user_mixin_inheritance():
    u = User(username='test', email='test@example.com')
    assert isinstance(u, UserMixin)
    assert u.is_authenticated
    assert u.is_active
    assert not u.is_anonymous

def test_user_representation():
    u = User(username='test', email='test@example.com')
    assert str(u) == '<User test>'

def test_soundboard_model():
    s = Soundboard(name='My Board', user_id=1, icon='fas fa-music')
    assert s.name == 'My Board'
    assert s.user_id == 1
    assert s.icon == 'fas fa-music'
    assert str(s) == '<Soundboard My Board>'

def test_sound_model():

    s = Sound(name='Explosion', soundboard_id=1, file_path='sounds/1/explosion.mp3', icon='fas fa-bomb')

    assert s.name == 'Explosion'

    assert s.soundboard_id == 1

    assert s.file_path == 'sounds/1/explosion.mp3'

    assert s.icon == 'fas fa-bomb'

    assert str(s) == '<Sound Explosion>'



def test_soundboard_crud():

    import os

    import sqlite3

    from config import Config

    

    # Use temporary DB

    db_path = 'test_soundboards_crud.sqlite3'

    if os.path.exists(db_path): os.remove(db_path)

    

    # Mock Config

    from app import Config as AppConfig

    original_db = AppConfig.SOUNDBOARDS_DB

    AppConfig.SOUNDBOARDS_DB = os.path.abspath(db_path)

    

    # Init DB

    with sqlite3.connect(db_path) as conn:

        with open('app/schema_soundboards.sql', 'r') as f:

            conn.executescript(f.read())

            

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

    

    # Cleanup

    AppConfig.SOUNDBOARDS_DB = original_db

    os.remove(db_path)



def test_sound_crud():

    import os

    import sqlite3

    from config import Config

    

    # Use temporary DB

    db_path = 'test_sounds_crud.sqlite3'

    if os.path.exists(db_path): os.remove(db_path)

    

    # Mock Config

    from app import Config as AppConfig

    original_db = AppConfig.SOUNDBOARDS_DB

    AppConfig.SOUNDBOARDS_DB = os.path.abspath(db_path)

    

    # Init DB

    with sqlite3.connect(db_path) as conn:

        with open('app/schema_soundboards.sql', 'r') as f:

            conn.executescript(f.read())

            

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

    

    # Cleanup

    AppConfig.SOUNDBOARDS_DB = original_db

    os.remove(db_path)
