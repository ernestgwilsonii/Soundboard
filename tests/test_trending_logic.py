from app.models import Rating, Soundboard, User


def test_get_trending_logic(client):
    with client.application.app_context():
        # Setup users
        u1 = User(username="trend_u1", email="trend_u1@t.com")
        u1.set_password("p")
        u1.save()
        u2 = User(username="trend_u2", email="trend_u2@t.com")
        u2.set_password("p")
        u2.save()

        assert u1.id is not None
        assert u2.id is not None

        # U1 follows U2 -> U2 (and its boards) gets 2 points
        u1.follow(u2.id)

        # Setup boards
        # sb1: high rating, 1 creator follower
        sb1 = Soundboard(name="High Rated", user_id=u1.id, is_public=True)
        sb1.save()
        Rating(user_id=u2.id, soundboard_id=sb1.id, score=5).save()

        # sb2: low rating, 0 creator followers
        sb2 = Soundboard(name="Low Rated", user_id=u2.id, is_public=True)
        sb2.save()
        Rating(user_id=u1.id, soundboard_id=sb2.id, score=1).save()

        trending = Soundboard.get_trending()

        assert trending[0].id == sb1.id
        assert trending[1].id == sb2.id
        assert len(trending) == 2
