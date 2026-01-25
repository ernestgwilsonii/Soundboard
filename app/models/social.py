"""Social interaction models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy.sql import func

from app.constants import DEFAULT_PAGE_SIZE, LARGE_PAGE_SIZE
from app.extensions import db_orm as db
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Rating(BaseModel):
    """Represents a user's rating of a soundboard."""

    __tablename__ = "ratings"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    soundboard_id = db.Column(
        db.Integer, db.ForeignKey("soundboards.id"), nullable=False, index=True
    )
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def save(self) -> None:
        """Save the rating to the database."""
        # Check for existing rating to update
        existing = Rating.query.filter_by(
            user_id=self.user_id, soundboard_id=self.soundboard_id
        ).first()
        if existing:
            existing.score = self.score
            db.session.commit()
            self.id = existing.id
        else:
            super().save()


class Comment(BaseModel):
    """Represents a comment on a soundboard."""

    __tablename__ = "comments"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    soundboard_id = db.Column(
        db.Integer, db.ForeignKey("soundboards.id"), nullable=False, index=True
    )
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def _from_row(cls, row: Any) -> Comment:
        """Helper to create a Comment instance from a database row."""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            soundboard_id=row["soundboard_id"],
            text=row["text"],
            created_at=row["created_at"],
        )

    def get_author_username(self) -> str:
        """Retrieve the username of the comment author."""
        from .user import User

        user = User.get_by_id(self.user_id)
        return user.username if user else "Unknown"

    def get_author(self) -> Optional["User"]:
        """Retrieve the User object of the comment author."""
        from .user import User

        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)


class Tag(BaseModel):
    """Represents a tag for categorization."""

    __tablename__ = "tags"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False, index=True)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def get_or_create(name: str) -> Optional[Tag]:
        """Retrieve a tag by name or create it if it doesn't exist."""
        name = name.lower().strip()
        if not name:
            return None
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.commit()
        return tag

    @staticmethod
    def get_all() -> List[Tag]:
        """Retrieve all tags."""
        return Tag.query.order_by(Tag.name.asc()).all()

    @staticmethod
    def get_popular(limit: int = DEFAULT_PAGE_SIZE) -> List[Tag]:
        """Retrieve the most popular tags based on usage."""
        from .soundboard import SoundboardTag

        stmt = (
            db.select(Tag, func.count(SoundboardTag.soundboard_id).label("count"))
            .join(SoundboardTag, Tag.id == SoundboardTag.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(SoundboardTag.soundboard_id).desc())
            .limit(limit)
        )

        result = db.session.execute(stmt).all()
        return [row[0] for row in result]


class Activity(BaseModel):
    """Represents a user activity record."""

    __tablename__ = "activities"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    action_type = db.Column(db.String(32))
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def record(user_id: int, action_type: str, description: str) -> None:
        """Record a new user activity."""
        activity = Activity(
            user_id=user_id, action_type=action_type, description=description
        )
        db.session.add(activity)
        db.session.commit()

    @staticmethod
    def get_recent(limit: int = LARGE_PAGE_SIZE) -> List[Activity]:
        """Retrieve recent activities."""
        return Activity.query.order_by(Activity.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_from_following(user_ids: List[int], limit: int = 10) -> List[Activity]:
        """Retrieve recent activities from a list of followed users."""
        if not user_ids:
            return []
        return (
            Activity.query.filter(Activity.user_id.in_(user_ids))
            .order_by(Activity.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_user(self) -> Optional["User"]:
        """Retrieve the user associated with this activity."""
        from .user import User

        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)


class Notification(BaseModel):
    """Represents a user notification."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    type = db.Column(db.String(32))
    message = db.Column(db.Text)
    link = db.Column(db.String(256), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def add(user_id: int, type: str, message: str, link: Optional[str] = None) -> None:
        """Create a new notification for a user."""
        notif = Notification(user_id=user_id, type=type, message=message, link=link)
        db.session.add(notif)
        db.session.commit()

    @staticmethod
    def get_unread_for_user(user_id: int) -> List[Notification]:
        """Retrieve all unread notifications for a user."""
        return (
            Notification.query.filter_by(user_id=user_id, is_read=False)
            .order_by(Notification.created_at.desc())
            .all()
        )

    @staticmethod
    def count_unread_for_user(user_id: int) -> int:
        """Count the number of unread notifications for a user."""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def mark_all_read(user_id: int) -> None:
        """Mark all notifications as read for a user."""
        db.session.query(Notification).filter_by(user_id=user_id, is_read=False).update(
            {"is_read": True}
        )
        db.session.commit()


class BoardCollaborator(BaseModel):
    """Represents a collaborator on a soundboard."""

    __tablename__ = "board_collaborators"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    soundboard_id = db.Column(
        db.Integer, db.ForeignKey("soundboards.id"), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, nullable=False, index=True)
    role = db.Column(db.String(32), default="editor")
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def get_for_board(soundboard_id: int) -> List[BoardCollaborator]:
        """Retrieve all collaborators for a specific soundboard."""
        return BoardCollaborator.query.filter_by(soundboard_id=soundboard_id).all()

    @staticmethod
    def get_by_user_and_board(
        user_id: int, soundboard_id: int
    ) -> Optional[BoardCollaborator]:
        """Retrieve a specific collaborator record."""
        return BoardCollaborator.query.filter_by(
            user_id=user_id, soundboard_id=soundboard_id
        ).first()

    def get_user(self) -> Optional["User"]:
        """Retrieve the User object for this collaborator."""
        from .user import User

        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)
