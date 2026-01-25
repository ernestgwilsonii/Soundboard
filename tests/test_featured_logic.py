from app.models import AdminSettings, Soundboard, User


def test_get_featured_explicit(app):
    with app.app_context():
        # Create a user and a soundboard
        u = User(username="testuser", email="test@example.com")
        u.set_password("password")
        u.save()

        sb1 = Soundboard(name="Board 1", user_id=u.id, is_public=True)
        sb1.save()
        sb2 = Soundboard(name="Board 2", user_id=u.id, is_public=True)
        sb2.save()

        # Set sb2 as featured
        AdminSettings.set_setting("featured_soundboard_id", str(sb2.id))

        featured = Soundboard.get_featured()
        assert featured is not None
        assert featured.id == sb2.id


def test_get_featured_fallback_no_setting(app):
    with app.app_context():
        u = User(username="testuser", email="test@example.com")
        u.set_password("password")
        u.save()

        sb1 = Soundboard(name="Old Board", user_id=u.id, is_public=True)
        sb1.save()
        # Simulate time passing by adding another board later
        sb2 = Soundboard(name="New Board", user_id=u.id, is_public=True)
        sb2.save()

        # featured_soundboard_id is NULL by default in schema

        featured = Soundboard.get_featured()
        assert featured is not None
        assert featured.id == sb2.id  # Should be the most recent one


def test_get_featured_fallback_invalid_id(app):
    with app.app_context():
        u = User(username="testuser", email="test@example.com")
        u.set_password("password")
        u.save()

        sb1 = Soundboard(name="Only Board", user_id=u.id, is_public=True)
        sb1.save()

        # Set featured to a non-existent ID
        AdminSettings.set_setting("featured_soundboard_id", "999")

        featured = Soundboard.get_featured()
        assert featured is not None
        assert featured.id == sb1.id  # Should fallback since 999 is invalid


def test_index_route_featured(app):
    client = app.test_client()
    with app.app_context():
        u = User(username="testuser", email="test@example.com")
        u.set_password("password")
        u.save()

        sb = Soundboard(name="Featured Board", user_id=u.id, is_public=True)
        sb.save()

        AdminSettings.set_setting("featured_soundboard_id", str(sb.id))

    response = client.get("/")
    assert response.status_code == 200
    assert b"Featured Board" in response.data
    assert b"Featured" in response.data
