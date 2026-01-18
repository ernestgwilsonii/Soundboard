"""Soundboard and Sound models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from .social import BoardCollaborator

from app.db import get_accounts_db, get_soundboards_db
from app.enums import Visibility
from app.models.soundboard_mixins import SoundboardDiscoveryMixin, SoundboardSocialMixin


class Soundboard(SoundboardSocialMixin, SoundboardDiscoveryMixin):
    """
    Represents a soundboard containing multiple sounds.

    Attributes:
        id (int): Unique identifier for the soundboard.
        name (str): Name of the soundboard.
        user_id (int): ID of the user who created the soundboard.
        icon (str): Path to the soundboard's icon.
        is_public (bool): Whether the soundboard is publicly visible.
        visibility (Visibility): Visibility status (PUBLIC or PRIVATE).
        theme_color (str): Hex color code for the theme.
        theme_preset (str): Name of the theme preset.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        user_id: Optional[int] = None,
        icon: Optional[str] = None,
        is_public: bool = False,
        theme_color: str = "#0d6efd",
        theme_preset: str = "default",
    ) -> None:
        """
        Initialize a new Soundboard instance.

        Args:
            id (int, optional): Soundboard ID.
            name (str, optional): Soundboard name.
            user_id (int, optional): Creator's user ID.
            icon (str, optional): Icon file path.
            is_public (bool, optional): Visibility status. Defaults to False.
            theme_color (str, optional): Theme color hex code. Defaults to "#0d6efd".
            theme_preset (str, optional): Theme preset name. Defaults to "default".
        """
        self.id = id
        self.name = name
        self.user_id = user_id
        self.icon = icon
        self.is_public = bool(is_public)
        self.theme_color = theme_color
        self.theme_preset = theme_preset

    @property
    def visibility(self) -> Visibility:
        """Get the visibility status as an enum."""
        return Visibility.PUBLIC if self.is_public else Visibility.PRIVATE

    @visibility.setter
    def visibility(self, value: Visibility) -> None:
        """Set the visibility status using an enum."""
        self.is_public = value == Visibility.PUBLIC

    def save(self) -> None:
        """
        Save the soundboard to the database.

        Inserts a new record if id is None, otherwise updates the existing record.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        if self.id is None:
            database_cursor.execute(
                "INSERT INTO soundboards (name, user_id, icon, is_public, theme_color, theme_preset) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    self.name,
                    self.user_id,
                    self.icon,
                    int(self.is_public),
                    self.theme_color,
                    self.theme_preset,
                ),
            )
            self.id = database_cursor.lastrowid
        else:
            database_cursor.execute(
                "UPDATE soundboards SET name=?, user_id=?, icon=?, is_public=?, theme_color=?, theme_preset=? WHERE id=?",
                (
                    self.name,
                    self.user_id,
                    self.icon,
                    int(self.is_public),
                    self.theme_color,
                    self.theme_preset,
                    self.id,
                ),
            )
        database_connection.commit()

    def delete(self) -> None:
        """Delete the soundboard and all associated sounds."""
        if self.id:
            database_connection = get_soundboards_db()
            database_cursor = database_connection.cursor()
            # Also delete associated sounds
            database_cursor.execute(
                "DELETE FROM sounds WHERE soundboard_id = ?", (self.id,)
            )
            database_cursor.execute("DELETE FROM soundboards WHERE id = ?", (self.id,))
            database_connection.commit()

    @classmethod
    def _from_row(cls, row: Any) -> Soundboard:
        """Helper to create a Soundboard instance from a database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            user_id=row["user_id"],
            icon=row["icon"],
            is_public=row["is_public"],
            theme_color=row["theme_color"],
            theme_preset=row["theme_preset"],
        )

    @staticmethod
    def get_by_id(soundboard_id: int) -> Optional[Soundboard]:
        """
        Retrieve a soundboard by its ID.

        Args:
            soundboard_id (int): The ID of the soundboard.

        Returns:
            Soundboard or None: The Soundboard object if found, else None.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT * FROM soundboards WHERE id = ?", (soundboard_id,)
        )
        row = database_cursor.fetchone()
        if row:
            return Soundboard._from_row(row)
        return None

    @staticmethod
    def get_all() -> List[Soundboard]:
        """
        Retrieve all soundboards.

        Returns:
            list[Soundboard]: A list of all Soundboard objects.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT * FROM soundboards ORDER BY name ASC")
        rows = database_cursor.fetchall()
        return [Soundboard._from_row(row) for row in rows]

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Soundboard]:
        """
        Retrieve all soundboards created by a specific user.

        Args:
            user_id (int): The user ID.

        Returns:
            list[Soundboard]: A list of Soundboard objects belonging to the user.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT * FROM soundboards WHERE user_id = ? ORDER BY name ASC", (user_id,)
        )
        rows = database_cursor.fetchall()
        return [Soundboard._from_row(row) for row in rows]

    @staticmethod
    def get_from_following(user_ids: List[int]) -> List[Soundboard]:
        """
        Retrieve public soundboards from a list of followed users.

        Args:
            user_ids (list[int]): List of followed user IDs.

        Returns:
            list[Soundboard]: A list of Soundboard objects.
        """
        if not user_ids:
            return []
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        placeholders = ",".join(["?"] * len(user_ids))
        database_cursor.execute(
            f"SELECT * FROM soundboards WHERE user_id IN ({placeholders}) AND is_public = 1 ORDER BY created_at DESC",  # nosec
            user_ids,
        )
        rows = database_cursor.fetchall()
        return [Soundboard._from_row(row) for row in rows]

    @staticmethod
    def get_public(order_by: str = "recent") -> List[Soundboard]:
        """
        Retrieve public soundboards.

        Args:
            order_by (str, optional): Sorting criteria ('recent', 'top', 'name', 'trending'). Defaults to "recent".

        Returns:
            list[Soundboard]: A list of public Soundboard objects.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()

        if order_by == "trending":
            return Soundboard.get_trending()

        sql = "SELECT * FROM soundboards WHERE is_public = 1"
        if order_by == "top":
            # Order by average rating
            sql = """
                SELECT soundboards.*, AVG(ratings.score) as avg_score
                FROM soundboards soundboards
                LEFT JOIN ratings ratings ON soundboards.id = ratings.soundboard_id
                WHERE soundboards.is_public = 1
                GROUP BY soundboards.id
                ORDER BY avg_score DESC, soundboards.name ASC
            """
        elif order_by == "name":
            sql += " ORDER BY name ASC"
        else:  # recent
            sql += " ORDER BY created_at DESC, id DESC"

        database_cursor.execute(sql)
        rows = database_cursor.fetchall()
        return [Soundboard._from_row(row) for row in rows]

    @staticmethod
    def get_by_tag(tag_name: str) -> List[Soundboard]:
        """
        Retrieve public soundboards associated with a specific tag.

        Args:
            tag_name (str): The name of the tag.

        Returns:
            list[Soundboard]: A list of Soundboard objects.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            """
            SELECT soundboards.* FROM soundboards soundboards
            JOIN soundboard_tags soundboard_tags ON soundboards.id = soundboard_tags.soundboard_id
            JOIN tags tags ON soundboard_tags.tag_id = tags.id
            WHERE tags.name = ? AND soundboards.is_public = 1
            ORDER BY soundboards.name ASC
        """,
            (tag_name.lower().strip(),),
        )
        rows = database_cursor.fetchall()
        return [Soundboard._from_row(row) for row in rows]

    @staticmethod
    def get_recent_public(limit: int = 6) -> List[Soundboard]:
        """
        Retrieve the most recently created public soundboards.

        Args:
            limit (int, optional): The maximum number of soundboards to return. Defaults to 6.

        Returns:
            list[Soundboard]: A list of Soundboard objects.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT * FROM soundboards WHERE is_public = 1 ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )
        rows = database_cursor.fetchall()
        return [Soundboard._from_row(row) for row in rows]

    def get_sounds(self) -> List[Sound]:
        """
        Retrieve all sounds associated with this soundboard.

        Returns:
            list[Sound]: A list of Sound objects.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT * FROM sounds WHERE soundboard_id = ? ORDER BY display_order ASC, name ASC",
            (self.id,),
        )
        rows = database_cursor.fetchall()
        return [Sound._from_row(row) for row in rows]

    def get_creator_username(self) -> str:
        """
        Retrieve the username of the soundboard's creator.

        Returns:
            str: The username.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT username FROM users WHERE id = ?", (self.user_id,)
        )
        row = database_cursor.fetchone()
        return str(row["username"]) if row else "Unknown"

    def get_collaborators(self) -> List["BoardCollaborator"]:
        """
        Retrieve all collaborators for the soundboard.

        Returns:
            list[BoardCollaborator]: A list of BoardCollaborator objects.
        """
        from .social import BoardCollaborator

        if self.id is None:
            return []
        return BoardCollaborator.get_for_board(self.id)

    def is_editor(self, user_id: int) -> bool:
        """
        Check if a user is an editor (or owner) of the soundboard.

        Args:
            user_id (int): The user ID.

        Returns:
            bool: True if user is owner or editor, False otherwise.
        """
        from app.models.social import BoardCollaborator

        if self.user_id == user_id:
            return True
        if self.id is None:
            return False
        collab = BoardCollaborator.get_by_user_and_board(user_id, self.id)
        return collab is not None and collab.role == "editor"

    def __repr__(self) -> str:
        return f"<Soundboard {self.name}>"


class Sound:
    """
    Represents a sound file within a soundboard.

    Attributes:
        id (int): Unique identifier for the sound.
        soundboard_id (int): ID of the parent soundboard.
        name (str): Display name of the sound.
        file_path (str): Relative path to the audio file.
        icon (str): Relative path to the sound icon.
        display_order (int): Order of the sound in the board.
        volume (float): Default volume level (0.0 to 1.0).
        is_loop (bool): Whether the sound should loop.
        start_time (float): Start time in seconds for playback.
        end_time (float): End time in seconds for playback.
        hotkey (str): Keyboard shortcut key.
        bitrate (int): Bitrate of the audio file.
        file_size (int): Size of the file in bytes.
        format (str): Audio format (e.g., 'mp3', 'wav').
    """

    def __init__(
        self,
        id: Optional[int] = None,
        soundboard_id: Optional[int] = None,
        name: Optional[str] = None,
        file_path: Optional[str] = None,
        icon: Optional[str] = None,
        display_order: int = 0,
        volume: float = 1.0,
        is_loop: bool = False,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        hotkey: Optional[str] = None,
        bitrate: Optional[int] = None,
        file_size: Optional[int] = None,
        format: Optional[str] = None,
    ) -> None:
        """
        Initialize a new Sound instance.

        Args:
            id (int, optional): Sound ID.
            soundboard_id (int, optional): Parent soundboard ID.
            name (str, optional): Sound name.
            file_path (str, optional): File path.
            icon (str, optional): Icon path.
            display_order (int, optional): Display order. Defaults to 0.
            volume (float, optional): Volume. Defaults to 1.0.
            is_loop (bool, optional): Loop status. Defaults to False.
            start_time (float, optional): Start time. Defaults to 0.0.
            end_time (float, optional): End time.
            hotkey (str, optional): Hotkey.
            bitrate (int, optional): Audio bitrate.
            file_size (int, optional): File size.
            format (str, optional): Audio format.
        """
        self.id = id
        self.soundboard_id = soundboard_id
        self.name = name
        self.file_path = file_path
        self.icon = icon
        self.display_order = display_order
        self.volume = volume
        self.is_loop = bool(is_loop)
        self.start_time = start_time
        self.end_time = end_time
        self.hotkey = hotkey
        self.bitrate = bitrate
        self.file_size = file_size
        self.format = format

    def save(self) -> None:
        """Save the sound to the database. Inserts if new, updates otherwise."""
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        if self.id is None:
            if self.display_order == 0:
                database_cursor.execute(
                    "SELECT MAX(display_order) FROM sounds WHERE soundboard_id = ?",
                    (self.soundboard_id,),
                )
                max_row = database_cursor.fetchone()
                max_order = max_row[0] if max_row and max_row[0] is not None else 0
                self.display_order = max_order + 1

            database_cursor.execute(
                "INSERT INTO sounds (soundboard_id, name, file_path, icon, display_order, volume, is_loop, start_time, end_time, hotkey, bitrate, file_size, format) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.soundboard_id,
                    self.name,
                    self.file_path,
                    self.icon,
                    self.display_order,
                    self.volume,
                    int(self.is_loop),
                    self.start_time,
                    self.end_time,
                    self.hotkey,
                    self.bitrate,
                    self.file_size,
                    self.format,
                ),
            )
            self.id = database_cursor.lastrowid
        else:
            database_cursor.execute(
                "UPDATE sounds SET soundboard_id=?, name=?, file_path=?, icon=?, display_order=?, volume=?, is_loop=?, start_time=?, end_time=?, hotkey=?, bitrate=?, file_size=?, format=? WHERE id=?",
                (
                    self.soundboard_id,
                    self.name,
                    self.file_path,
                    self.icon,
                    self.display_order,
                    self.volume,
                    int(self.is_loop),
                    self.start_time,
                    self.end_time,
                    self.hotkey,
                    self.bitrate,
                    self.file_size,
                    self.format,
                    self.id,
                ),
            )
        database_connection.commit()

    def delete(self) -> None:
        """Delete the sound and its associated files from the filesystem."""
        if self.id:
            import os

            from flask import current_app

            database_connection = get_soundboards_db()
            database_cursor = database_connection.cursor()

            if self.file_path:
                full_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], self.file_path
                )
                if os.path.exists(full_path):
                    os.remove(full_path)

            if self.icon and "/" in self.icon:
                icon_full_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], self.icon
                )
                if os.path.exists(icon_full_path):
                    os.remove(icon_full_path)

            database_cursor.execute("DELETE FROM sounds WHERE id = ?", (self.id,))
            database_connection.commit()

    @classmethod
    def _from_row(cls, row: Any) -> Sound:
        """Helper to create a Sound instance from a database row."""
        return cls(
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
            hotkey=row["hotkey"],
            bitrate=row["bitrate"],
            file_size=row["file_size"],
            format=row["format"],
        )

    @staticmethod
    def get_by_id(sound_id: int) -> Optional[Sound]:
        """
        Retrieve a sound by its ID.

        Args:
            sound_id (int): The ID of the sound.

        Returns:
            Sound or None: The Sound object if found, else None.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT * FROM sounds WHERE id = ?", (sound_id,))
        row = database_cursor.fetchone()
        if row:
            return Sound._from_row(row)
        return None

    @staticmethod
    def reorder_multiple(soundboard_id: int, sound_ids: List[int]) -> None:
        """
        Update the display order for multiple sounds.

        Args:
            soundboard_id (int): The ID of the soundboard.
            sound_ids (list[int]): List of sound IDs in the new order.
        """
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        for index, sound_id in enumerate(sound_ids):
            database_cursor.execute(
                "UPDATE sounds SET display_order = ? WHERE id = ? AND soundboard_id = ?",
                (index + 1, sound_id, soundboard_id),
            )
        database_connection.commit()

    def __repr__(self) -> str:
        return f"<Sound {self.name}>"
