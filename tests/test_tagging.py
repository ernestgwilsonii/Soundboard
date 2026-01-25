from app.models import Soundboard, Tag, User


def test_tagging_logic(app):
    with app.app_context():
        u = User(username="tagger", email="t@example.com")
        u.set_password("p")
        u.save()

        sb = Soundboard(name="Tag Board", user_id=u.id, is_public=True)
        sb.save()

        # Add tags
        sb.add_tag("fun")
        sb.add_tag("meme ")  # Should be normalized

        tags = sb.get_tags()
        assert len(tags) == 2
        assert tags[0].name == "fun"
        assert tags[1].name == "meme"

        # Test popularity
        sb2 = Soundboard(name="Another Board", user_id=u.id, is_public=True)
        sb2.save()
        sb2.add_tag("fun")

        popular = Tag.get_popular()
        assert popular[0].name == "fun"

        # Remove tag
        sb.remove_tag("meme")
        assert len(sb.get_tags()) == 1
