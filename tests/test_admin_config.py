from app.enums import UserRole
from app.models import AdminSettings, User


def test_admin_settings_persistence(app):
    with app.app_context():
        # Test Maintenance Mode
        AdminSettings.set_setting("maintenance_mode", "1")
        assert AdminSettings.get_setting("maintenance_mode") == "1"

        AdminSettings.set_setting("maintenance_mode", "0")
        assert AdminSettings.get_setting("maintenance_mode") == "0"

        # Test Announcement
        AdminSettings.set_setting("announcement_message", "Test Banner")
        AdminSettings.set_setting("announcement_type", "warning")

        assert AdminSettings.get_setting("announcement_message") == "Test Banner"
        assert AdminSettings.get_setting("announcement_type") == "warning"


def test_settings_route_updates(app):
    client = app.test_client()

    with app.app_context():
        u = User(username="admin", email="admin@example.com", role=UserRole.ADMIN)
        u.set_password("pass")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "admin", "password": "pass", "submit": "Sign In"},
    )

    response = client.post(
        "/admin/settings",
        data={
            "featured_soundboard_id": "1",
            "announcement_message": "Route Test",
            "announcement_type": "danger",
            "maintenance_mode": "y",  # WTForms boolean logic usually takes 'y' or 'on'
            "submit": "Save Settings",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Settings updated" in response.data

    with app.app_context():
        assert AdminSettings.get_setting("announcement_message") == "Route Test"
        assert AdminSettings.get_setting("maintenance_mode") == "1"

    # Test disabling maintenance mode
    client.post(
        "/admin/settings",
        data={
            "featured_soundboard_id": "1",
            "announcement_message": "Route Test",
            "announcement_type": "danger",
            # maintenance_mode missing means False
            "submit": "Save Settings",
        },
        follow_redirects=True,
    )

    with app.app_context():
        assert AdminSettings.get_setting("maintenance_mode") == "0"


def test_announcement_banner_visibility(app):
    client = app.test_client()

    with app.app_context():
        # No banner initially
        AdminSettings.set_setting("announcement_message", "")

    response = client.get("/")
    assert b"alert-" not in response.data

    with app.app_context():
        # Set banner
        AdminSettings.set_setting("announcement_message", "Global Alert Test")
        AdminSettings.set_setting("announcement_type", "danger")

    response = client.get("/")
    assert b"Global Alert Test" in response.data
    assert b"alert-danger" in response.data


def test_maintenance_mode_enforcement(app):
    client = app.test_client()

    # Enable maintenance mode
    with app.app_context():
        AdminSettings.set_setting("maintenance_mode", "1")

    # Anonymous user should see maintenance
    response = client.get("/")
    assert b"Under Maintenance" in response.data

    # Login as normal user
    with app.app_context():
        u = User(username="user", email="user@example.com", role=UserRole.USER)
        u.set_password("pass")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "user", "password": "pass", "submit": "Sign In"},
    )

    # Normal user should see maintenance
    response = client.get("/")
    assert b"Under Maintenance" in response.data

    # Login as admin
    with app.app_context():
        a = User(username="admin2", email="admin2@example.com", role=UserRole.ADMIN)
        a.set_password("pass")
        a.save()

    client.get("/auth/logout")
    client.post(
        "/auth/login",
        data={"username": "admin2", "password": "pass", "submit": "Sign In"},
    )

    # Admin should bypass maintenance
    response = client.get("/")
    assert b"Under Maintenance" not in response.data
    assert b"Soundboard" in response.data
