from app.models import User


def test_login_with_username_and_email(client):
    with client.application.app_context():
        u = User(username="testuser", email="test@example.com", is_verified=True)
        u.set_password("password")
        u.save()

    # Test login with username
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Logout" in response.data

    # Logout
    client.get("/auth/logout")

    # Test login with email
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Logout" in response.data
