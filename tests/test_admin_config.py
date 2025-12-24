import pytest
from app import create_app
import os
import sqlite3
from config import Config
from app.models import AdminSettings

@pytest.fixture
def app_context(monkeypatch):
    accounts_db = os.path.abspath('test_accounts_config.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_config.sqlite3')
    
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
        yield app
        
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_admin_settings_persistence(app_context):
    with app_context.app_context():
        # Test Maintenance Mode
        AdminSettings.set_setting('maintenance_mode', '1')
        assert AdminSettings.get_setting('maintenance_mode') == '1'
        
        AdminSettings.set_setting('maintenance_mode', '0')
        assert AdminSettings.get_setting('maintenance_mode') == '0'
        
        # Test Announcement
        AdminSettings.set_setting('announcement_message', 'Test Banner')
        AdminSettings.set_setting('announcement_type', 'warning')
        
        assert AdminSettings.get_setting('announcement_message') == 'Test Banner'
        assert AdminSettings.get_setting('announcement_type') == 'warning'

def test_settings_route_updates(app_context):
    client = app_context.test_client()
    from app.models import User
    
    with app_context.app_context():
        u = User(username='admin', email='admin@example.com', role='admin')
        u.set_password('pass')
        u.save()
        
    client.post('/auth/login', data={'username': 'admin', 'password': 'pass', 'submit': 'Sign In'})
    
    response = client.post('/admin/settings', data={
        'featured_soundboard_id': '1',
        'announcement_message': 'Route Test',
        'announcement_type': 'danger',
        'maintenance_mode': 'y', # WTForms boolean logic usually takes 'y' or 'on'
        'submit': 'Save Settings'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Settings updated' in response.data
    
    with app_context.app_context():
        assert AdminSettings.get_setting('announcement_message') == 'Route Test'
        assert AdminSettings.get_setting('maintenance_mode') == '1'
        
    # Test disabling maintenance mode
    client.post('/admin/settings', data={
        'featured_soundboard_id': '1',
        'announcement_message': 'Route Test',
        'announcement_type': 'danger',
        # maintenance_mode missing means False
        'submit': 'Save Settings'
    }, follow_redirects=True)
    
    
    with app_context.app_context():
        assert AdminSettings.get_setting('maintenance_mode') == '0'

def test_announcement_banner_visibility(app_context):
    client = app_context.test_client()
    from app.models import AdminSettings
    
    with app_context.app_context():
        # No banner initially
        AdminSettings.set_setting('announcement_message', '')
        
    response = client.get('/')
    assert b'alert-' not in response.data
    
    with app_context.app_context():
        # Set banner
        AdminSettings.set_setting('announcement_message', 'Global Alert Test')
        AdminSettings.set_setting('announcement_type', 'danger')
        
    response = client.get('/')
    assert b'Global Alert Test' in response.data
    assert b'alert-danger' in response.data
