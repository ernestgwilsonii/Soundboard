from app.models import User


def test_user_follow_unfollow(client):
    with client.application.app_context():
        u1 = User(username="user1", email="u1@test.com")
        u1.set_password("pass1")
        u1.save()
        u2 = User(username="user2", email="u2@test.com")
        u2.set_password("pass2")
        u2.save()

        assert u1.id is not None
        assert u2.id is not None

        # Test follow
        u1.follow(u2.id)
        assert u1.is_following(u2.id) is True
        assert u2.get_follower_count() == 1
        assert u1.get_following_count() == 1

        # Test following list
        following = u1.get_following()
        assert len(following) == 1
        assert following[0].id == u2.id

        # Test followers list
        followers = u2.get_followers()
        assert len(followers) == 1
        assert followers[0].id == u1.id

        # Test unfollow
        u1.unfollow(u2.id)
        assert u1.is_following(u2.id) is False
        assert u2.get_follower_count() == 0
        assert u1.get_following_count() == 0
