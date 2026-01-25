from app.models import Soundboard, User


def test_share_button_presence(client):
    with client.application.app_context():
        u = User(username="shareuser", email="share@example.com")
        u.set_password("pass")
        u.save()
        sb = Soundboard(name="Shareable Board", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None
        sb_id = sb.id

    response = client.get(f"/soundboard/view/{sb_id}")
    assert b"Share" in response.data
    assert b"shareBoard()" in response.data
    assert b"share-toast" in response.data


def test_share_button_absence_private(client):
    with client.application.app_context():
        u = User(username="privateuser", email="private@example.com")
        u.set_password("pass")
        u.save()
        sb = Soundboard(name="Private Board", user_id=u.id, is_public=False)
        sb.save()
        assert sb.id is not None
        sb_id = sb.id

    # Need to be logged in to view private board
    with client.application.app_context():
        # Mock login not needed if we just check page content?
        # No, view route redirects if private and not owner.
        pass

    # Login
    client.post(
        "/auth/login",
        data={"username": "privateuser", "password": "cat", "submit": "Sign In"},
    )  # Oh wait user has no password set in this test setup?
    # Let's fix user setup

    with client.application.app_context():
        u_login = User.get_by_username("privateuser")
        assert u_login is not None
        u_login.set_password("pass")
        u_login.save()

    client.post(
        "/auth/login",
        data={"username": "privateuser", "password": "pass", "submit": "Sign In"},
    )

    response = client.get(f"/soundboard/view/{sb_id}")
    assert b"Share" not in response.data
    assert b'id="share-btn"' not in response.data
