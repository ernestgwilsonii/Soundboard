"""Soundboard and Sound models."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, List

from flask import current_app
from sqlalchemy.sql import func

from app.enums import Visibility
from app.extensions import db_orm as db
from app.models.base import BaseModel
from app.models.soundboard_mixins import SoundboardDiscoveryMixin, SoundboardSocialMixin


class SoundboardTag(BaseModel):
    """Association model for Soundboard and Tag."""

    __tablename__ = "soundboard_tags"
    __bind_key__ = "soundboards"
    soundboard_id = db.Column(
        db.Integer, db.ForeignKey("soundboards.id"), primary_key=True
    )
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), primary_key=True)


if TYPE_CHECKING:
    from .social import BoardCollaborator


class Soundboard(BaseModel, SoundboardSocialMixin, SoundboardDiscoveryMixin):
    """Represents a soundboard containing multiple sounds."""

    __tablename__ = "soundboards"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    icon = db.Column(db.String(64))
    is_public = db.Column(db.Boolean, default=False, index=True)
    theme_color = db.Column(db.String(7), default="#0d6efd")
    theme_preset = db.Column(db.String(32), default="default")
    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    sounds = db.relationship(
        "Sound", backref="soundboard", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @property
    def visibility(self) -> Visibility:
        """Get the visibility status as an enum."""
        return Visibility.PUBLIC if self.is_public else Visibility.PRIVATE

    @visibility.setter
    def visibility(self, value: Visibility) -> None:
        """Set the visibility status using an enum."""
        self.is_public = value == Visibility.PUBLIC

    def delete(self) -> None:
        """Delete the soundboard and all associated sounds."""
        # 1. Delete all sounds (triggers Sound.delete logic if iterated, but SQLAlchemy cascade handles DB rows)
        # However, Sound.delete() has file cleanup logic.
        # SQLAlchemy cascade='all, delete-orphan' does NOT call the delete() method of the child object automatically
        # unless we hook into events.
        # For simplicity, we manually delete children to ensure file cleanup.
        for sound in self.sounds.all():
            sound.delete()

        # 2. Delete self
        super().delete()

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Soundboard]:
        """Retrieve all soundboards created by a specific user."""
        return (
            Soundboard.query.filter_by(user_id=user_id)
            .order_by(Soundboard.name.asc())
            .all()
        )

    @staticmethod
    def get_from_following(user_ids: List[int]) -> List[Soundboard]:
        """Retrieve public soundboards from a list of followed users."""
        if not user_ids:
            return []
        return (
            Soundboard.query.filter(Soundboard.user_id.in_(user_ids))
            .filter_by(is_public=True)
            .order_by(Soundboard.created_at.desc())
            .all()
        )

    @staticmethod
    def get_public(order_by: str = "recent") -> List[Soundboard]:
        """Retrieve public soundboards."""
        if order_by == "trending":
            return Soundboard.get_trending()

        query = Soundboard.query.filter_by(is_public=True)

        if order_by == "top":
            # This requires joining with Ratings in the Mixin/separate query or refactoring.
            # Since `SoundboardDiscoveryMixin` relies on raw SQL for complex stats,
            # we might delegate to it or implement a simpler version here if possible.
            # But the mixin methods are static.
            # Let's keep it consistent: Use the mixin logic if complex, or simple sort.
            # For now, let's implement basic sorting here.
            # "top" sort is complex (requires join). Let's use the mixin's `search` logic or similar?
            # Actually, `get_public` was using raw SQL.
            # We can implement 'top' using SQLAlchemy:
            # We need Rating model (not yet migrated).
            # So for now, we might need to rely on Mixin methods OR migrate Rating first.
            # Let's defer 'top' sort or implement it suboptimally until Rating is migrated.
            # Or assume Rating will be migrated soon.
            # Let's fall back to recent for safety until Rating is migrated.
            return query.order_by(
                Soundboard.created_at.desc(), Soundboard.id.desc()
            ).all()
        elif order_by == "name":
            query = query.order_by(Soundboard.name.asc())
        else:  # recent
            query = query.order_by(Soundboard.created_at.desc(), Soundboard.id.desc())

        return query.all()

    @staticmethod
    def get_by_tag(tag_name: str) -> List[Soundboard]:
        """Retrieve public soundboards associated with a specific tag."""
        from .social import Tag

        stmt = (
            db.select(Soundboard.id)
            .join(SoundboardTag, Soundboard.id == SoundboardTag.soundboard_id)
            .join(Tag, SoundboardTag.tag_id == Tag.id)
            .where(Tag.name == tag_name.lower().strip())
            .where(Soundboard.is_public.is_(True))
            .order_by(Soundboard.name.asc())
        )
        result = db.session.execute(stmt)
        ids = [row[0] for row in result]
        if not ids:
            return []

        return (
            Soundboard.query.filter(Soundboard.id.in_(ids))
            .order_by(Soundboard.name.asc())
            .all()
        )

    @staticmethod
    def get_recent_public(limit: int = 6) -> List[Soundboard]:
        """Retrieve the most recently created public soundboards."""
        return (
            Soundboard.query.filter_by(is_public=True)
            .order_by(Soundboard.created_at.desc(), Soundboard.id.desc())
            .limit(limit)
            .all()
        )

    def get_sounds(self) -> List[Sound]:
        """Retrieve all sounds associated with this soundboard."""
        return self.sounds.order_by(Sound.display_order.asc(), Sound.name.asc()).all()

    def get_creator_username(self) -> str:
        """Retrieve the username of the soundboard's creator."""
        from app.models.user import User

        user = User.get_by_id(self.user_id)
        return user.username if user else "Unknown"

    def get_collaborators(self) -> List["BoardCollaborator"]:
        """Retrieve all collaborators for the soundboard."""
        from .social import BoardCollaborator

        if self.id is None:
            return []
        return BoardCollaborator.get_for_board(self.id)

    def is_editor(self, user_id: int) -> bool:
        """Check if a user is an editor (or owner) of the soundboard."""
        from app.models.social import BoardCollaborator

        if self.user_id == user_id:
            return True
        if self.id is None:
            return False
        collab = BoardCollaborator.get_by_user_and_board(user_id, self.id)
        return collab is not None and collab.role == "editor"

    def __repr__(self) -> str:
        return f"<Soundboard {self.name}>"


class Sound(BaseModel):
    """Represents a sound file within a soundboard."""

    __tablename__ = "sounds"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    soundboard_id = db.Column(
        db.Integer, db.ForeignKey("soundboards.id"), nullable=False, index=True
    )
    name = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    icon = db.Column(db.String(64))
    display_order = db.Column(db.Integer, default=0)
    volume = db.Column(db.Float, default=1.0)
    is_loop = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.Float, default=0.0)
    end_time = db.Column(db.Float, nullable=True)
    hotkey = db.Column(db.String(1), nullable=True)
    bitrate = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    format = db.Column(db.String(10), nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def save(self) -> None:
        """Save the sound to the database. Inserts if new, updates otherwise."""
        if self.id is None and (self.display_order == 0 or self.display_order is None):
            # Auto-assign display order
            max_order = (
                db.session.query(db.func.max(Sound.display_order))
                .filter_by(soundboard_id=self.soundboard_id)
                .scalar()
            )
            self.display_order = (max_order or 0) + 1
        super().save()

    def delete(self) -> None:
        """Delete the sound and its associated files from the filesystem."""
        if self.file_path:
            full_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], self.file_path
            )
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except OSError:
                    pass

        if self.icon and "/" in self.icon:
            icon_full_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], self.icon
            )
            if os.path.exists(icon_full_path):
                try:
                    os.remove(icon_full_path)
                except OSError:
                    pass

        super().delete()

    @staticmethod
    def reorder_multiple(soundboard_id: int, sound_ids: List[int]) -> None:
        """Update the display order for multiple sounds."""
        for index, sound_id in enumerate(sound_ids):
            sound = Sound.query.get(sound_id)
            if sound and sound.soundboard_id == soundboard_id:
                sound.display_order = index + 1
        db.session.commit()

    def __repr__(self) -> str:
        return f"<Sound {self.name}>"
