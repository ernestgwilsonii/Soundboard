from app.models import User


def test_admin_toggle_verify(client):
    with client.application.app_context():
        # Create admin
        admin = User(
            username="admin_v", email="admin_v@test.com", role="admin", is_verified=True
        )
        admin.set_password("admin")
        admin.save()

        # Create unverified user
        user = User(username="user_v", email="user_v@test.com", is_verified=False)
        user.set_password("user")
        user.save()
        assert user.id is not None
        user_id = user.id

    # Login as admin
    client.post("/auth/login", data={"username": "admin_v", "password": "admin"})

    # Toggle verification
    response = client.post(
        f"/admin/user/{user_id}/toggle_verified", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"is now verified" in response.data

    with client.application.app_context():
        u = User.get_by_id(user_id)
        assert u is not None
        assert u.is_verified is True

    # Toggle back
    response = client.post(
        f"/admin/user/{user_id}/toggle_verified", follow_redirects=True
    )
    assert b"is now unverified" in response.data

    with client.application.app_context():
        u = User.get_by_id(user_id)
        assert u is not None
        assert u.is_verified is False
