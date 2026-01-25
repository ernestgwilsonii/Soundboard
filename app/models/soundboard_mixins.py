"""Mixins for decomposing the Soundboard model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from app.models.social import Comment, Tag
    from .soundboard import Soundboard

from app.constants import DEFAULT_PAGE_SIZE
from app.extensions import db_orm as db


class SoundboardSocialMixin:
    """Handles social interactions like ratings, comments, and tagging."""

    id: Any

    def get_average_rating(self) -> Dict[str, Union[float, int]]:
        """Calculate average rating."""
        from app.models.social import Rating

        result = (
            db.session.query(db.func.avg(Rating.score), db.func.count(Rating.id))
            .filter_by(soundboard_id=self.id)
            .first()
        )

        avg, count = result if result else (0, 0)
        return {
            "average": round(avg, 1) if avg else 0,
            "count": count if count else 0,
        }

    def get_user_rating(self, user_id: int) -> int:
        """Get rating for a specific user."""
        from app.models.social import Rating

        rating = Rating.query.filter_by(soundboard_id=self.id, user_id=user_id).first()
        return int(rating.score) if rating else 0

    def get_comments(self) -> List["Comment"]:
        """Get all comments."""
        from app.models.social import Comment

        return (
            Comment.query.filter_by(soundboard_id=self.id)
            .order_by(Comment.created_at.desc())
            .all()
        )

    def get_tags(self) -> List["Tag"]:
        """Get all tags."""
        from app.models.social import Tag
        from app.models.soundboard import SoundboardTag

        stmt = (
            db.select(Tag)
            .join(SoundboardTag, Tag.id == SoundboardTag.tag_id)
            .where(SoundboardTag.soundboard_id == self.id)
            .order_by(Tag.name.asc())
        )

        return db.session.execute(stmt).scalars().all()

    def add_tag(self, tag_name: str) -> None:
        """Add a tag."""
        from app.models.social import Tag
        from app.models.soundboard import SoundboardTag

        tag = Tag.get_or_create(tag_name)
        if not tag:
            return

        # Check if already tagged
        exists = SoundboardTag.query.filter_by(
            soundboard_id=self.id, tag_id=tag.id
        ).first()

        if not exists:
            new_tag = SoundboardTag(soundboard_id=self.id, tag_id=tag.id)
            db.session.add(new_tag)
            db.session.commit()

    def remove_tag(self, tag_name: str) -> None:
        """Remove a tag."""
        from app.models.social import Tag
        from app.models.soundboard import SoundboardTag

        tag = Tag.query.filter_by(name=tag_name.lower().strip()).first()
        if tag:
            SoundboardTag.query.filter_by(soundboard_id=self.id, tag_id=tag.id).delete()
            db.session.commit()


class SoundboardDiscoveryMixin:
    """Handles search, trending, and featured board discovery."""

    @staticmethod
    def get_trending(limit: int = DEFAULT_PAGE_SIZE) -> List[Soundboard]:
        """Get trending boards."""
        import app.models.soundboard as sb_models
        from app.models.social import Rating
        from app.models.user import User

        # 1. Get average scores and counts using SQLAlchemy
        # We join Soundboard with Rating
        stmt = (
            db.select(
                sb_models.Soundboard,
                db.func.avg(Rating.score).label("avg_score"),
                db.func.count(Rating.id).label("rating_count"),
            )
            .filter(sb_models.Soundboard.is_public.is_(True))
            .outerjoin(Rating)
            .group_by(sb_models.Soundboard.id)
        )

        results = db.session.execute(stmt).all()

        scored_soundboards = []
        for soundboard, avg_rating, rating_count in results:
            avg_rating = avg_rating or 0
            rating_count = rating_count or 0

            user = User.get_by_id(soundboard.user_id)
            follower_count = user.get_follower_count() if user else 0

            # Use the same scoring formula: (avg_rating * rating_count) + (follower_count * 2)
            score = (avg_rating * rating_count) + (follower_count * 2)
            scored_soundboards.append((soundboard, score))

        scored_soundboards.sort(
            key=lambda x: (x[1], x[0].created_at, x[0].id), reverse=True
        )
        return [x[0] for x in scored_soundboards[:limit]]

    @staticmethod
    def get_featured() -> Optional[Soundboard]:
        """Get featured board."""
        import app.models.soundboard as sb_models
        from app.models.admin import AdminSettings

        featured_id_string = AdminSettings.get_setting("featured_soundboard_id")
        if featured_id_string:
            featured_soundboard = sb_models.Soundboard.get_by_id(
                int(featured_id_string)
            )
            if featured_soundboard and featured_soundboard.is_public:
                return featured_soundboard

        trending_soundboards = SoundboardDiscoveryMixin.get_trending(limit=1)
        return trending_soundboards[0] if trending_soundboards else None

    @staticmethod
    def search(query_string: str, order_by: str = "recent") -> List[Soundboard]:
        """Search boards."""
        import app.models.soundboard as sb_models
        from app.models.social import Tag
        from app.models.soundboard import SoundboardTag
        from app.models.user import User

        # 1. Search users by name
        users = User.query.filter(User.username.like(f"%{query_string}%")).all()
        user_ids = [u.id for u in users]

        # 2. Search sounds by name to get soundboard IDs
        sounds = sb_models.Sound.query.filter(
            sb_models.Sound.name.like(f"%{query_string}%")
        ).all()
        ids_from_sounds = [s.soundboard_id for s in sounds]

        # 3. Search tags by name to get soundboard IDs
        tags = Tag.query.filter(Tag.name.like(f"%{query_string}%")).all()
        tag_ids = [t.id for t in tags]

        ids_from_tags = []
        if tag_ids:
            # Query the association table via model
            results = SoundboardTag.query.filter(
                SoundboardTag.tag_id.in_(tag_ids)
            ).all()
            ids_from_tags = [r.soundboard_id for r in results]

        # 4. Build the final query for soundboards
        query = sb_models.Soundboard.query.filter_by(is_public=True)

        # Build OR conditions
        filters = [sb_models.Soundboard.name.like(f"%{query_string}%")]
        if user_ids:
            filters.append(sb_models.Soundboard.user_id.in_(user_ids))
        if ids_from_sounds:
            filters.append(sb_models.Soundboard.id.in_(ids_from_sounds))
        if ids_from_tags:
            filters.append(sb_models.Soundboard.id.in_(ids_from_tags))

        from sqlalchemy import or_

        query = query.filter(or_(*filters))

        # 5. Handle ordering
        if order_by == "top":
            from app.models.social import Rating

            # Join with ratings and calculate average
            query = (
                query.outerjoin(Rating)
                .group_by(sb_models.Soundboard.id)
                .order_by(
                    db.func.avg(Rating.score).desc(), sb_models.Soundboard.name.asc()
                )
            )
        elif order_by == "name":
            query = query.order_by(sb_models.Soundboard.name.asc())
        else:  # recent
            query = query.order_by(
                sb_models.Soundboard.created_at.desc(), sb_models.Soundboard.id.desc()
            )

        return query.all()
