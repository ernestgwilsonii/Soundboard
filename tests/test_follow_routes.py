from app.models import User


def test_follow_unfollow_routes(client):
    with client.application.app_context():
        u1 = User(username="follower", email="f@test.com", is_verified=True)
        u1.set_password("pass")
        u1.save()
        u2 = User(username="followed", email="d@test.com", is_verified=True)
        u2.set_password("pass")
        u2.save()

    # Login
    client.post("/auth/login", data={"username": "follower", "password": "pass"})

    # Follow
    response = client.post("/auth/follow/followed", follow_redirects=True)
    assert response.status_code == 200
    assert b"You are now following followed" in response.data

    with client.application.app_context():
        u1_obj = User.get_by_username("follower")
        u2_obj = User.get_by_username("followed")
        assert u1_obj is not None
        assert u2_obj is not None
        assert u2_obj.id is not None
        assert u1_obj.is_following(u2_obj.id) is True

    # Unfollow
    response = client.post("/auth/unfollow/followed", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have unfollowed followed" in response.data

    with client.application.app_context():
        u1_obj = User.get_by_username("follower")
        u2_obj = User.get_by_username("followed")
        assert u1_obj is not None
        assert u2_obj is not None
        assert u2_obj.id is not None
        assert u1_obj.is_following(u2_obj.id) is False


def test_follow_self_fails(client):
    with client.application.app_context():
        u1 = User(username="self", email="s@test.com", is_verified=True)
        u1.set_password("pass")
        u1.save()

    client.post("/auth/login", data={"username": "self", "password": "pass"})

    response = client.post("/auth/follow/self", follow_redirects=True)
    assert b"You cannot follow yourself" in response.data


def test_follow_button_rendering(client):
    with client.application.app_context():
        u1 = User(username="user1", email="u1@test.com", is_verified=True)
        u1.set_password("pass")
        u1.save()
        u2 = User(username="user2", email="u2@test.com", is_verified=True)
        u2.set_password("pass")
        u2.save()

    # Not logged in - no button
    response = client.get("/auth/user/user2")
    assert b'btn-primary px-4">Follow</button>' not in response.data

    # Logged in as user1
    client.post("/auth/login", data={"username": "user1", "password": "pass"})
    response = client.get("/auth/user/user2")
    assert b'btn-primary px-4">Follow</button>' in response.data

    # Follow user2
    client.post("/auth/follow/user2")
    response = client.get("/auth/user/user2")
    assert b'btn-outline-danger px-4">Unfollow</button>' in response.data


def test_members_list_route(client):
    with client.application.app_context():
        u1 = User(username="member1", email="m1@test.com", is_verified=True)
        u1.set_password("pass")
        u1.save()
        u2 = User(username="member2", email="m2@test.com", is_verified=True)
        u2.set_password("pass")
        u2.save()

    # Unauthenticated
    response = client.get("/auth/members", follow_redirects=True)
    assert b"Sign In" in response.data

    # Authenticated
    client.post("/auth/login", data={"username": "member1", "password": "pass"})
    response = client.get("/auth/members")
    assert response.status_code == 200
    assert b"member1" in response.data
    assert b"member2" in response.data


def test_members_search_and_pagination(client):
    with client.application.app_context():
        u1 = User(username="alice", email="a@test.com", is_verified=True)
        u1.set_password("pass")
        u1.save()
        u2 = User(username="bob", email="b@test.com", is_verified=True)
        u2.set_password("pass")
        u2.save()

    client.post("/auth/login", data={"username": "alice", "password": "pass"})

    # Search for 'bob'
    response = client.get("/auth/members?q=bob")
    # Use card-title to be sure we are looking at the result grid, not navbar
    assert b'card-title mb-1">bob</h5>' in response.data
    assert b'card-title mb-1">alice</h5>' not in response.data

    # Pagination test (limit 1)
    response = client.get("/auth/members?limit=1")
    assert response.status_code == 200
    # Should only show one user (plus stats/nav)
    # Check if there's a link to page 2
    assert b"page=2" in response.data


def test_follower_following_lists(client):
    with client.application.app_context():
        u1 = User(username="user_a", email="a@test.com", is_verified=True)
        u1.set_password("pass")
        u1.save()
        u2 = User(username="user_b", email="b@test.com", is_verified=True)
        u2.set_password("pass")
        u2.save()
        assert u2.id is not None
        u1.follow(u2.id)

    client.post("/auth/login", data={"username": "user_a", "password": "pass"})

    # Check following list for user_a
    response = client.get("/auth/user/user_a/following")
    assert response.status_code == 200
    assert b"user_b" in response.data

    # Check followers list for user_b
    response = client.get("/auth/user/user_b/followers")
    assert response.status_code == 200
    assert b"user_a" in response.data
