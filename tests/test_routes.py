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
