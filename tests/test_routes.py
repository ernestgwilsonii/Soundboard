import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
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
