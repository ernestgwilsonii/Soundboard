"""Tests for sound reordering and playback fields persistence."""

from app.models import Sound, Soundboard, User


def test_sound_default_ordering(app):
    """Test default sound ordering when sounds are added to a board."""
    with app.app_context():
        u = User(username="test", email="test@example.com")
        u.set_password("pass")
        u.save()
        assert u.id is not None

        sb = Soundboard(name="Order Board", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None

        s1 = Sound(soundboard_id=sb.id, name="First", file_path="1/1.mp3")
        s1.save()
        assert s1.display_order == 1

        s2 = Sound(soundboard_id=sb.id, name="Second", file_path="1/2.mp3")
        s2.save()
        assert s2.display_order == 2

        # Verify retrieval order
        sounds = sb.get_sounds()
        assert sounds[0].name == "First"
        assert sounds[1].name == "Second"


def test_explicit_ordering(app):
    """Test sound retrieval based on explicit display_order."""
    with app.app_context():
        u = User(username="test2", email="test2@example.com")
        u.set_password("pass")
        u.save()
        assert u.id is not None

        sb = Soundboard(name="Explicit Board", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None

        # Create sounds with explicit swapped orders
        s1 = Sound(
            soundboard_id=sb.id, name="Later", file_path="1/1.mp3", display_order=10
        )
        s1.save()

        s2 = Sound(
            soundboard_id=sb.id, name="Earlier", file_path="1/2.mp3", display_order=5
        )
        s2.save()

        sounds = sb.get_sounds()
        assert sounds[0].name == "Earlier"
        assert sounds[1].name == "Later"


def test_reorder_api(app):
    """Test the sound reordering API endpoint."""
    client = app.test_client()
    from app.models import Sound, Soundboard, User

    with app.app_context():
        u = User(username="reorder", email="reorder@example.com")
        u.set_password("pass")
        u.save()
        assert u.id is not None

        from app.models import AdminSettings

        AdminSettings.set_setting("maintenance_mode", "0")

        sb = Soundboard(name="API Board", user_id=u.id, is_public=True)
        sb.save()
        sb_id = sb.id
        assert sb_id is not None

        s1 = Sound(soundboard_id=sb_id, name="S1", file_path="1/1.mp3")
        s1.save()
        s2 = Sound(soundboard_id=sb_id, name="S2", file_path="1/2.mp3")
        s2.save()

        s1_id = s1.id
        assert s1_id is not None
        s2_id = s2.id
        assert s2_id is not None

    login_resp = client.post(
        "/auth/login",
        data={"username": "reorder", "password": "pass", "submit": "Sign In"},
        follow_redirects=True,
    )
    assert b"Logout" in login_resp.data

    # Send new order (S2 first)
    response = client.post(f"/soundboard/{sb_id}/reorder", json={"ids": [s2_id, s1_id]})
    assert response.status_code == 200

    with app.app_context():
        sb_loaded = Soundboard.get_by_id(sb_id)
        assert sb_loaded is not None
        sounds = sb_loaded.get_sounds()
        assert sounds[0].id == s2_id
        assert sounds[1].id == s1_id
        assert sounds[0].display_order == 1
        assert sounds[1].display_order == 2


def test_playback_fields_persistence(app):
    """Test that volume, loop, and time fields are correctly persisted."""
    with app.app_context():
        u = User(username="pb", email="pb@example.com")
        u.set_password("p")
        u.save()
        assert u.id is not None

        sb = Soundboard(name="PB Board", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None

        s = Sound(
            soundboard_id=sb.id,
            name="S",
            file_path="1/1.mp3",
            volume=0.5,
            is_loop=True,
            start_time=1.5,
            end_time=10.0,
        )
        s.save()
        sid = s.id
        assert sid is not None

    with app.app_context():
        s_loaded = Sound.get_by_id(sid)
        assert s_loaded is not None
        assert s_loaded.volume == 0.5
        assert s_loaded.is_loop is True
        assert s_loaded.start_time == 1.5
        assert s_loaded.end_time == 10.0
