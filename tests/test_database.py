def test_load_user(app):
    from app import login

    with app.app_context():
        from app.models import User

        u = User(username="loader", email="loader@example.com")
        u.set_password("hash")
        u.save()

        # Explicitly cast ID to string as Flask-Login expects
        user = login._user_callback(str(u.id))
        assert user is not None
        assert user.username == "loader"
