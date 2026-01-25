from app.models import User
from app.models.admin import AdminSettings


def test_admin_settings_access_denied_for_user(client):
    # Create a regular user
    with client.application.app_context():
        u = User(username="regularuser", email="user@example.com", role="user")
        u.set_password("password")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "regularuser", "password": "password", "submit": "Sign In"},
    )
    response = client.get("/admin/settings", follow_redirects=True)
    # Depending on how admin_required is implemented, it might redirect to index with a flash message
    assert response.status_code == 200
    assert (
        b"You do not have permission" in response.data or response.request.path == "/"
    )


def test_admin_settings_access_allowed_for_admin(client):
    # Create an admin user
    with client.application.app_context():
        u = User(username="adminuser", email="admin@example.com", role="admin")
        u.set_password("password")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "adminuser", "password": "password", "submit": "Sign In"},
    )
    response = client.get("/admin/settings")
    assert response.status_code == 200
    assert b"Admin Settings" in response.data


def test_update_featured_soundboard(client, app):
    # Create an admin user
    with client.application.app_context():
        u = User(username="adminuser2", email="admin2@example.com", role="admin")
        u.set_password("password")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "adminuser2", "password": "password", "submit": "Sign In"},
    )

    # Post to update featured soundboard
    response = client.post(
        "/admin/settings",
        data={"featured_soundboard_id": "5", "submit": "Save Settings"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Settings updated" in response.data

    # Verify in DB
    with app.app_context():
        assert AdminSettings.get_setting("featured_soundboard_id") == "5"
