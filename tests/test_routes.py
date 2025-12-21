import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_index_route(client):
    # This should return a 200 OK once the route and template are implemented
    response = client.get('/')
    assert response.status_code == 200
    assert b"Soundboard" in response.data

def test_auth_blueprint_registered(client):
    from flask import url_for
    # This should not raise an error if registered
    with client.application.test_request_context():
        login_url = url_for('auth.login')
        assert login_url == '/auth/login'

def test_registration_flow(client):
    # This test will check if registration successfully adds a user
    import sqlite3
    from config import Config
    
    # Ensure user doesn't exist
    with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
        conn.execute("DELETE FROM users WHERE username = ?", ('newuser',))
    
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password',
        'password_confirm': 'password',
        'submit': 'Register'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Congratulations, you are now a registered user!" in response.data
    
    # Verify in DB
    with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", ('newuser',))
        user = cur.fetchone()
        assert user is not None
        assert user['email'] == 'newuser@example.com'

def test_login_flow(client):
    from app.models import User
    import sqlite3
    from config import Config
    
    # Ensure user doesn't exist
    with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
        conn.execute("DELETE FROM users WHERE username = ?", ('loginuser',))
    
    # Create a user first
    u = User(username='loginuser', email='login@example.com')
    u.set_password('cat')
    u.save()
    
    response = client.post('/auth/login', data={
        'username': 'loginuser',
        'password': 'cat',
        'submit': 'Sign In'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Check if we are redirected to index and user is logged in
    # (Since we don't have user info on index yet, we can check for logout link later)
    # For now, just check if it doesn't stay on login page with error
    assert b"Invalid username or password" not in response.data
    assert b"Sign In" not in response.data # Should not be on login page anymore
