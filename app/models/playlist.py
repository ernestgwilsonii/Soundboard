"""Playlist models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from sqlalchemy.sql import func

from app.extensions import db_orm as db
from app.models.base import BaseModel

if TYPE_CHECKING:
    from .soundboard import Sound


class PlaylistItem(BaseModel):
    """Represents an item in a playlist (mapping between playlist and sound)."""

    __tablename__ = "playlist_items"
    __bind_key__ = "soundboards"

    playlist_id = db.Column(db.Integer, db.ForeignKey("playlists.id"), primary_key=True)
    sound_id = db.Column(db.Integer, db.ForeignKey("sounds.id"), primary_key=True)
    display_order = db.Column(db.Integer, default=0)

    # Relationships
    sound = db.relationship("Sound")


class Playlist(BaseModel):
    """Represents a playlist of sounds."""

    __tablename__ = "playlists"
    __bind_key__ = "soundboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    items = db.relationship(
        "PlaylistItem",
        backref="playlist",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="PlaylistItem.display_order",
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Playlist]:
        """Retrieve all playlists created by a specific user."""
        return (
            Playlist.query.filter_by(user_id=user_id)
            .order_by(Playlist.name.asc())
            .all()
        )

    def get_sounds(self) -> List["Sound"]:
        """Retrieve all sounds in the playlist."""
        return [item.sound for item in self.items.all()]

    def add_sound(self, sound_id: int) -> None:
        """Add a sound to the playlist."""
        # Calculate next order
        max_order = (
            db.session.query(func.max(PlaylistItem.display_order))
            .filter_by(playlist_id=self.id)
            .scalar()
        )
        order = (max_order or 0) + 1

        item = PlaylistItem(playlist_id=self.id, sound_id=sound_id, display_order=order)
        db.session.add(item)
        db.session.commit()

    def remove_sound(self, sound_id: int) -> None:
        """Remove a sound from the playlist."""
        PlaylistItem.query.filter_by(playlist_id=self.id, sound_id=sound_id).delete()
        db.session.commit()
