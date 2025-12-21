import pytest
from app import create_app
import os
import sqlite3
from config import Config

@pytest.fixture
def client(monkeypatch):
    # Use temporary DBs for route tests
    accounts_db = os.path.abspath('test_accounts_routes.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_routes.sqlite3')
    
    # Patch Config before app creation
    monkeypatch.setattr(Config, 'ACCOUNTS_DB', accounts_db)
    monkeypatch.setattr(Config, 'SOUNDBOARDS_DB', soundboards_db)
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Initialize test DBs
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
        
    # Cleanup
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Soundboard" in response.data

def test_auth_blueprint_registered(client):
    from flask import url_for
    with client.application.test_request_context():
        login_url = url_for('auth.login')
        assert login_url == '/auth/login'

def test_registration_flow(client):
    # Registration flow should redirect to login upon success
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password',
        'password_confirm': 'password',
        'submit': 'Register'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Sign In" in response.data

def test_login_flow(client):
    from app.models import User
    with client.application.app_context():
        u = User(username='loginuser', email='login@example.com')
        u.set_password('cat')
        u.save()
    
    response = client.post('/auth/login', data={
        'username': 'loginuser',
        'password': 'cat',
        'submit': 'Sign In'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Logout" in response.data

def test_logout_flow(client):
    from app.models import User
    with client.application.app_context():
        u = User(username='logoutuser', email='logout@example.com')
        u.set_password('cat')
        u.save()
    
    client.post('/auth/login', data={'username': 'logoutuser', 'password': 'cat', 'submit': 'Sign In'})
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_profile_protected(client):
    response = client.get('/auth/profile', follow_redirects=True)
    assert b"Sign In" in response.data
    
    from app.models import User
    with client.application.app_context():
        u = User(username='profileuser', email='profile@example.com')
        u.set_password('cat')
        u.save()
    
    client.post('/auth/login', data={'username': 'profileuser', 'password': 'cat', 'submit': 'Sign In'})
    response = client.get('/auth/profile')
    assert response.status_code == 200
    assert b"User: profileuser" in response.data

def test_soundboard_blueprint_registered(client):
    from flask import url_for
    with client.application.test_request_context():
        create_url = url_for('soundboard.create')
        assert create_url == '/soundboard/create'

def test_soundboard_creation_flow(client):
    from app.models import User
    with client.application.app_context():
        u = User(username='sbuser', email='sb@example.com')
        u.set_password('cat')
        u.save()
            
    client.post('/auth/login', data={'username': 'sbuser', 'password': 'cat', 'submit': 'Sign In'})
    
    response = client.post('/soundboard/create', data={
        'name': 'Test SB',
        'icon': 'fas fa-test',
        'submit': 'Save'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'My Soundboards' in response.data
    assert b'Test SB' in response.data

def test_soundboard_edit_flow(client):
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='edituser', email='edit@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='Old Name', user_id=u.id, icon='old-icon')
        s.save()
        sb_id = s.id
            
    client.post('/auth/login', data={'username': 'edituser', 'password': 'cat', 'submit': 'Sign In'})
    
    response = client.post(f'/soundboard/edit/{sb_id}', data={
        'name': 'New Name',
        'icon': 'new-icon',
        'submit': 'Save'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'My Soundboards' in response.data
    assert b'New Name' in response.data
    
    with client.application.app_context():
        s_updated = Soundboard.get_by_id(sb_id)
        assert s_updated.name == 'New Name'

def test_soundboard_delete_flow(client):
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='deluser', email='del@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='To Delete', user_id=u.id, icon='del-icon')
        s.save()
        sb_id = s.id
            
    client.post('/auth/login', data={'username': 'deluser', 'password': 'cat', 'submit': 'Sign In'})
    
    response = client.post(f'/soundboard/delete/{sb_id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Soundboard deleted.' in response.data
    
    with client.application.app_context():
        assert Soundboard.get_by_id(sb_id) is None

def test_sound_upload_flow(client):
    from app.models import User, Soundboard, Sound
    import io
    
    with client.application.app_context():
        u = User(username='upuser', email='up@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='Upload Board', user_id=u.id)
        s.save()
        sb_id = s.id
            
    client.post('/auth/login', data={'username': 'upuser', 'password': 'cat', 'submit': 'Sign In'})
    
    data = {
        'name': 'Test Sound',
        'audio_file': (io.BytesIO(b"fake audio data"), 'test.mp3'),
        'icon': 'fas fa-volume-up',
        'submit': 'Upload'
    }
    
    response = client.post(f'/soundboard/{sb_id}/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Edit Soundboard' in response.data # Redirected back to edit page
    
    with client.application.app_context():
        sbs = Soundboard.get_by_id(sb_id)
        sounds = sbs.get_sounds()
        assert len(sounds) == 1
        assert sounds[0].name == 'Test Sound'
        assert sounds[0].file_path.endswith('test.mp3')
        sound_id = sounds[0].id
        
    # Delete sound
    response = client.post(f'/soundboard/sound/{sound_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sound deleted.' in response.data
    
    with client.application.app_context():
        assert Sound.get_by_id(sound_id) is None

def test_soundboard_view_route(client):
    from app.models import User, Soundboard, Sound
    with client.application.app_context():
        u = User(username='viewuser', email='view@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='View Board', user_id=u.id)
        s.save()
        snd = Sound(soundboard_id=s.id, name='View Sound', file_path='1/test.mp3')
        snd.save()
        sb_id = s.id
            
    response = client.get(f'/soundboard/view/{sb_id}')
    assert response.status_code == 200
    assert b'View Board' in response.data
    assert b'View Sound' in response.data
        