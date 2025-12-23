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
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='sbuser', email='sb@example.com')
        u.set_password('cat')
        u.save()
            
    client.post('/auth/login', data={'username': 'sbuser', 'password': 'cat', 'submit': 'Sign In'})
    
    response = client.post('/soundboard/create', data={
        'name': 'Test SB',
        'icon': 'fas fa-test',
        'is_public': True,
        'submit': 'Save'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'My Soundboards' in response.data
    assert b'Test SB' in response.data

def test_gallery_route(client):
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='galleryuser', email='gallery@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='Public Gallery Board', user_id=u.id, is_public=True)
        s.save()
        
    response = client.get('/soundboard/gallery')
    assert response.status_code == 200
    assert b'Public Gallery Board' in response.data

def test_search_route(client):
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='searchuser', email='search@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='Find Me Board', user_id=u.id, is_public=True)
        s.save()
        
    response = client.get('/soundboard/search?q=Find')
    assert response.status_code == 200
    assert b'Find Me Board' in response.data

def test_view_access_control(client):
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='owner', email='owner@example.com')
        u.set_password('cat')
        u.save()
        
        public_sb = Soundboard(name='Public View', user_id=u.id, is_public=True)
        public_sb.save()
        pub_id = public_sb.id
        
        private_sb = Soundboard(name='Private View', user_id=u.id, is_public=False)
        private_sb.save()
        priv_id = private_sb.id
        
    # Anonymous access to public board
    response = client.get(f'/soundboard/view/{pub_id}')
    assert response.status_code == 200
    assert b'Public View' in response.data
    
    # Anonymous access to private board (should redirect or error)
    response = client.get(f'/soundboard/view/{priv_id}', follow_redirects=True)
    assert response.status_code == 200 # Redirected to index
    assert b'Private View' not in response.data
    
    # Authenticated access to own private board
    client.post('/auth/login', data={'username': 'owner', 'password': 'cat', 'submit': 'Sign In'})
    response = client.get(f'/soundboard/view/{priv_id}')
    assert response.status_code == 200
    assert b'Private View' in response.data

def test_admin_required_logic(client):
    from app.models import User
    with client.application.app_context():
        # Create regular user
        u1 = User(username='reguser', email='reg@e.com')
        u1.set_password('cat')
        u1.save()
        # Create admin user
        u2 = User(username='adminuser', email='admin@e.com', role='admin')
        u2.set_password('cat')
        u2.save()
        
    # Test route protection (we'll check if it redirects non-admins)
    # We'll use a route that we know uses admin_required or mock it.
    # For now, let's just test the logic via a temporary route in the blueprint if needed,
    # or wait until Phase 2 when the real route exists.
    # Actually, let's implement User.get_all first.

def test_admin_required_decorator(client):
    from app.models import User
    with client.application.app_context():
        # Create regular user
        u1 = User(username='reguser', email='reg@e.com')
        u1.set_password('cat')
        u1.save()
        # Create admin user
        u2 = User(username='adminuser', email='admin@e.com', role='admin')
        u2.set_password('cat')
        u2.save()
        
    # Test route protection (we'll use a dummy admin route)
    # First, login as regular user
    client.post('/auth/login', data={'username': 'reguser', 'password': 'cat', 'submit': 'Sign In'})
    response = client.get('/admin/users', follow_redirects=True)
    assert b'You do not have permission to access this page.' in response.data
    
    # Login as admin user
    client.get('/auth/logout', follow_redirects=True)
    client.post('/auth/login', data={'username': 'adminuser', 'password': 'cat', 'submit': 'Sign In'}, follow_redirects=True)
    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b'User Management' in response.data
    assert b'reguser' in response.data
    assert b'adminuser' in response.data

def test_toggle_user_active_flow(client):
    from app.models import User
    with client.application.app_context():
        u = User(username='tgluser', email='tgl@e.com')
        u.set_password('cat')
        u.save()
        user_id = u.id
        
        a = User(username='tgladmin', email='tgla@e.com', role='admin')
        a.set_password('cat')
        a.save()
        
    client.post('/auth/login', data={'username': 'tgladmin', 'password': 'cat', 'submit': 'Sign In'})
    
    # Toggle to inactive
    response = client.post(f'/admin/user/{user_id}/toggle_active', follow_redirects=True)
    assert b'has been disabled' in response.data
    with client.application.app_context():
        u2 = User.get_by_id(user_id)
        assert u2.active is False
        
    # Toggle back to active
    response = client.post(f'/admin/user/{user_id}/toggle_active', follow_redirects=True)
    assert b'has been enabled' in response.data
    with client.application.app_context():
        u3 = User.get_by_id(user_id)
        assert u3.active is True

def test_toggle_user_role_flow(client):
    from app.models import User
    with client.application.app_context():
        u = User(username='roleuser', email='role@e.com', role='user')
        u.set_password('cat')
        u.save()
        user_id = u.id
        
        a = User(username='roleadmin', email='rolea@e.com', role='admin')
        a.set_password('cat')
        a.save()
        
    client.post('/auth/login', data={'username': 'roleadmin', 'password': 'cat', 'submit': 'Sign In'})
    
    # Toggle to admin
    response = client.post(f'/admin/user/{user_id}/toggle_role', follow_redirects=True)
    assert b'role changed to admin' in response.data
    with client.application.app_context():
        u2 = User.get_by_id(user_id)
        assert u2.role == 'admin'
        
    # Toggle back to user
    response = client.post(f'/admin/user/{user_id}/toggle_role', follow_redirects=True)
    assert b'role changed to user' in response.data
    with client.application.app_context():
        u3 = User.get_by_id(user_id)
        assert u3.role == 'user'

def test_admin_password_reset_flow(client):
    from app.models import User
    with client.application.app_context():
        u = User(username='resetuser', email='reset@e.com')
        u.set_password('oldpass')
        u.save()
        user_id = u.id
        
        a = User(username='resetadmin', email='reseta@e.com', role='admin')
        a.set_password('cat')
        a.save()
        
    client.post('/auth/login', data={'username': 'resetadmin', 'password': 'cat', 'submit': 'Sign In'})
    
    # Reset password
    response = client.post(f'/admin/user/{user_id}/reset_password', data={
        'password': 'newpassword',
        'password_confirm': 'newpassword',
        'submit': 'Reset Password'
    }, follow_redirects=True)
    
    assert b'has been reset' in response.data
    
    # Verify new password works
    client.get('/auth/logout', follow_redirects=True)
    response = client.post('/auth/login', data={'username': 'resetuser', 'password': 'newpassword', 'submit': 'Sign In'}, follow_redirects=True)
    assert b'Logout' in response.data

def test_soundboard_edit_flow(client):
    from app.models import User, Soundboard
    with client.application.app_context():
        u = User(username='edituser', email='edit@example.com')
        u.set_password('cat')
        u.save()
        s = Soundboard(name='Old Name', user_id=u.id, icon='old-icon', is_public=False)
        s.save()
        sb_id = s.id
            
    client.post('/auth/login', data={'username': 'edituser', 'password': 'cat', 'submit': 'Sign In'})
    
    response = client.post(f'/soundboard/edit/{sb_id}', data={
        'name': 'New Name',
        'icon': 'new-icon',
        'is_public': True,
        'submit': 'Save'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'My Soundboards' in response.data
    assert b'New Name' in response.data
    
    with client.application.app_context():
        s_updated = Soundboard.get_by_id(sb_id)
        assert s_updated.name == 'New Name'
        assert s_updated.is_public is True

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
        s = Soundboard(name='View Board', user_id=u.id, is_public=True)
        s.save()
        snd = Sound(soundboard_id=s.id, name='View Sound', file_path='1/test.mp3')
        snd.save()
        sb_id = s.id
            
    response = client.get(f'/soundboard/view/{sb_id}')
    assert response.status_code == 200
    assert b'View Board' in response.data
    assert b'View Sound' in response.data
        