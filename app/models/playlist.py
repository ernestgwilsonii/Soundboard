"""Playlist models."""

from __future__ import annotations

from typing import List, Optional

from app.db import get_soundboards_db


class Playlist:
    """
    Represents a playlist of sounds.

    Attributes:
        id (int): Unique identifier for the playlist.
        user_id (int): ID of the user who created the playlist.
        name (str): Name of the playlist.
        description (str): Description of the playlist.
        is_public (bool): Whether the playlist is public.
        created_at (str): Timestamp of creation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.is_public = bool(is_public)
        self.created_at = created_at

    def save(self) -> None:
        """Save the playlist to the database."""
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO playlists (user_id, name, description, is_public) VALUES (?, ?, ?, ?)",
                (self.user_id, self.name, self.description, int(self.is_public)),
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE playlists SET name=?, description=?, is_public=? WHERE id=?",
                (self.name, self.description, int(self.is_public), self.id),
            )
        db.commit()

    def delete(self) -> None:
        """Delete the playlist and its items."""
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            cur.execute("DELETE FROM playlist_items WHERE playlist_id = ?", (self.id,))
            cur.execute("DELETE FROM playlists WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(playlist_id: int) -> Optional[Playlist]:
        """
        Retrieve a playlist by its ID.

        Args:
            playlist_id (int): The playlist ID.

        Returns:
            Playlist or None: The Playlist object if found.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
        row = cur.fetchone()
        if row:
            return Playlist(
                id=row["id"],
                user_id=row["user_id"],
                name=row["name"],
                description=row["description"],
                is_public=row["is_public"],
                created_at=row["created_at"],
            )
        return None

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Playlist]:
        """
        Retrieve all playlists created by a specific user.

        Args:
            user_id (int): The user ID.

        Returns:
            list[Playlist]: A list of Playlist objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM playlists WHERE user_id = ? ORDER BY name ASC", (user_id,)
        )
        rows = cur.fetchall()
        return [
            Playlist(
                id=row["id"],
                user_id=row["user_id"],
                name=row["name"],
                description=row["description"],
                is_public=row["is_public"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_sounds(self) -> List:
        """
        Retrieve all sounds in the playlist.

        Returns:
            list[Sound]: A list of Sound objects.
        """
        from app.models.soundboard import Sound

        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            """
            SELECT s.* FROM sounds s
            JOIN playlist_items pi ON s.id = pi.sound_id
            WHERE pi.playlist_id = ?
            ORDER BY pi.display_order ASC
        """,
            (self.id,),
        )
        rows = cur.fetchall()
        return [
            Sound(
                id=row["id"],
                soundboard_id=row["soundboard_id"],
                name=row["name"],
                file_path=row["file_path"],
                icon=row["icon"],
                display_order=row["display_order"],
                volume=row["volume"],
                is_loop=row["is_loop"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                bitrate=row["bitrate"],
                file_size=row["file_size"],
                format=row["format"],
            )
            for row in rows
        ]

    def add_sound(self, sound_id: int) -> None:
        """
        Add a sound to the playlist.

        Appends the sound to the end of the playlist.

        Args:
            sound_id (int): The ID of the sound to add.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT MAX(display_order) FROM playlist_items WHERE playlist_id = ?",
            (self.id,),
        )
        max_row = cur.fetchone()
        order = (max_row[0] + 1) if max_row and max_row[0] is not None else 1

        cur.execute(
            "INSERT INTO playlist_items (playlist_id, sound_id, display_order) VALUES (?, ?, ?)",
            (self.id, sound_id, order),
        )
        db.commit()

    def remove_sound(self, sound_id: int) -> None:
        """
        Remove a sound from the playlist.

        Args:
            sound_id (int): The ID of the sound to remove.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "DELETE FROM playlist_items WHERE playlist_id = ? AND sound_id = ?",
            (self.id, sound_id),
        )
        db.commit()


class PlaylistItem:
    """
    Represents an item in a playlist (mapping between playlist and sound).

    Attributes:
        id (int): Unique identifier.
        playlist_id (int): ID of the playlist.
        sound_id (int): ID of the sound.
        display_order (int): Order in the playlist.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        playlist_id: Optional[int] = None,
        sound_id: Optional[int] = None,
        display_order: int = 0,
    ):
        self.id = id
        self.playlist_id = playlist_id
        self.sound_id = sound_id
        self.display_order = display_order
