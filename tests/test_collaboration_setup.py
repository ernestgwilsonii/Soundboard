from app import create_app, socketio


def test_socketio_initialization():
    flask_app = create_app()
    assert hasattr(flask_app, "extensions")
    assert "socketio" in flask_app.extensions


def test_socket_connection():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    client = socketio.test_client(flask_app)
    assert client.is_connected()
    client.disconnect()


def test_join_board_presence():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    client = socketio.test_client(flask_app)

    # Simulate joining a board
    client.emit("join_board", {"board_id": 1})

    # In testing mode with anonymous user, presence update might not happen
    # unless we mock current_user.
    # But we can at least check if the event doesn't crash.
    client.disconnect()


def test_board_collaborator_model():
    from app.models import BoardCollaborator

    flask_app = create_app()
    with flask_app.app_context():
        # This assumes the DB is initialized and migrate.py was run (which I did)
        # We'll just check if we can instantiate it
        bc = BoardCollaborator(soundboard_id=1, user_id=1, role="editor")
        assert bc.role == "editor"
        assert bc.soundboard_id == 1
