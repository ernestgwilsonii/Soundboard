from app.models import Comment, Rating, Soundboard, User


def test_ratings_model(app):
    with app.app_context():
        u1 = User(username="u1", email="u1@example.com", is_verified=True)
        u1.set_password("p")
        u1.save()
        u2 = User(username="u2", email="u2@example.com", is_verified=True)
        u2.set_password("p")
        u2.save()

        sb = Soundboard(name="Social Board", user_id=u1.id, is_public=True)
        sb.save()

        # Add ratings
        r1 = Rating(user_id=u1.id, soundboard_id=sb.id, score=5)
        r1.save()

        r2 = Rating(user_id=u2.id, soundboard_id=sb.id, score=3)
        r2.save()

        # Verify average
        stats = sb.get_average_rating()
        assert stats["average"] == 4.0
        assert stats["count"] == 2

        # Update rating
        r1.score = 4
        r1.save()
        stats = sb.get_average_rating()
        assert stats["average"] == 3.5


def test_comments_model(app):
    with app.app_context():
        u = User(username="commenter", email="c@example.com", is_verified=True)
        u.set_password("p")
        u.save()

        sb = Soundboard(name="Comment Board", user_id=u.id, is_public=True)
        sb.save()

        c = Comment(user_id=u.id, soundboard_id=sb.id, text="Great board!")
        c.save()

        comments = sb.get_comments()
        assert len(comments) == 1
        assert comments[0].text == "Great board!"
        assert comments[0].get_author_username() == "commenter"

        # Delete comment
        comments[0].delete()
        assert len(sb.get_comments()) == 0


def test_rating_api(app):
    client = app.test_client()
    with app.app_context():
        u = User(username="rater", email="r@example.com", is_verified=True)
        u.set_password("p")
        u.save()
        sb = Soundboard(name="Rate Me", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None
        sb_id = sb.id

    client.post(
        "/auth/login", data={"username": "rater", "password": "p", "submit": "Sign In"}
    )

    # Post rating
    response = client.post(f"/soundboard/{sb_id}/rate", json={"score": 5})
    assert response.status_code == 200
    data = response.get_json()
    assert data["average"] == 5.0
    assert data["count"] == 1

    # Update rating
    response = client.post(f"/soundboard/{sb_id}/rate", json={"score": 1})
    data = response.get_json()
    assert data["average"] == 1.0
    assert data["count"] == 1


def test_comment_routes(app):
    client = app.test_client()
    with app.app_context():
        u = User(username="commenter2", email="c2@example.com", is_verified=True)
        u.set_password("p")
        u.save()
        sb = Soundboard(name="Comment Route Board", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None
        sb_id = sb.id

    client.post(
        "/auth/login",
        data={"username": "commenter2", "password": "p", "submit": "Sign In"},
    )

    # Post comment
    response = client.post(
        f"/soundboard/{sb_id}/comment",
        data={"text": "Route Comment"},
        follow_redirects=True,
    )
    assert b"Comment posted!" in response.data
    assert b"Route Comment" in response.data

    # Verify DB
    with app.app_context():
        comment = Comment.get_by_id(1)
        assert comment is not None
        assert comment.text == "Route Comment"
        comment_id = comment.id

    # Delete comment
    response = client.post(
        f"/soundboard/comment/{comment_id}/delete", follow_redirects=True
    )
    assert b"Comment deleted" in response.data

    with client.application.app_context():
        sb_final = Soundboard.get_by_id(sb_id)
        assert sb_final is not None
        assert len(sb_final.get_comments()) == 0
