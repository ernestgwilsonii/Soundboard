"""Soundboard and Sound models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    from app.models.social import BoardCollaborator, Comment, Tag

from app.constants import DEFAULT_PAGE_SIZE
from app.db import get_accounts_db, get_soundboards_db
from app.enums import Visibility


class Soundboard:
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
    ):
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
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
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
            self.id = cur.lastrowid
        else:
            cur.execute(
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
        db.commit()

    def delete(self) -> None:
        """Delete the soundboard and all associated sounds."""
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            # Also delete associated sounds
            cur.execute("DELETE FROM sounds WHERE soundboard_id = ?", (self.id,))
            cur.execute("DELETE FROM soundboards WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(soundboard_id: int) -> Optional[Soundboard]:
        """
        Retrieve a soundboard by its ID.

        Args:
            soundboard_id (int): The ID of the soundboard.

        Returns:
            Soundboard or None: The Soundboard object if found, else None.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE id = ?", (soundboard_id,))
        row = cur.fetchone()
        if row:
            return Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
        return None

    @staticmethod
    def get_all() -> List[Soundboard]:
        """
        Retrieve all soundboards.

        Returns:
            list[Soundboard]: A list of all Soundboard objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards ORDER BY name ASC")
        rows = cur.fetchall()
        return [
            Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
            for row in rows
        ]

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Soundboard]:
        """
        Retrieve all soundboards created by a specific user.

        Args:
            user_id (int): The user ID.

        Returns:
            list[Soundboard]: A list of Soundboard objects belonging to the user.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM soundboards WHERE user_id = ? ORDER BY name ASC", (user_id,)
        )
        rows = cur.fetchall()
        return [
            Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
            for row in rows
        ]

    @staticmethod
    def get_public(order_by: str = "recent") -> List[Soundboard]:
        """
        Retrieve public soundboards.

        Args:
            order_by (str, optional): Sorting criteria ('recent', 'top', 'name', 'trending'). Defaults to "recent".

        Returns:
            list[Soundboard]: A list of public Soundboard objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()

        if order_by == "trending":
            return Soundboard.get_trending()

        sql = "SELECT * FROM soundboards WHERE is_public = 1"
        if order_by == "top":
            # Order by average rating
            sql = """
                SELECT s.*, AVG(r.score) as avg_score
                FROM soundboards s
                LEFT JOIN ratings r ON s.id = r.soundboard_id
                WHERE s.is_public = 1
                GROUP BY s.id
                ORDER BY avg_score DESC, s.name ASC
            """
        elif order_by == "name":
            sql += " ORDER BY name ASC"
        else:  # recent
            sql += " ORDER BY created_at DESC, id DESC"

        cur.execute(sql)
        rows = cur.fetchall()
        return [
            Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
            for row in rows
        ]

    @staticmethod
    def get_by_tag(tag_name: str) -> List[Soundboard]:
        """
        Retrieve public soundboards associated with a specific tag.

        Args:
            tag_name (str): The name of the tag.

        Returns:
            list[Soundboard]: A list of Soundboard objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            """
            SELECT s.* FROM soundboards s
            JOIN soundboard_tags st ON s.id = st.soundboard_id
            JOIN tags t ON st.tag_id = t.id
            WHERE t.name = ? AND s.is_public = 1
            ORDER BY s.name ASC
        """,
            (tag_name.lower().strip(),),
        )
        rows = cur.fetchall()
        return [
            Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
            for row in rows
        ]

    @staticmethod
    def get_recent_public(limit: int = 6) -> List[Soundboard]:
        """
        Retrieve the most recently created public soundboards.

        Args:
            limit (int, optional): The maximum number of soundboards to return. Defaults to 6.

        Returns:
            list[Soundboard]: A list of Soundboard objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM soundboards WHERE is_public = 1 ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
            for row in rows
        ]

    @staticmethod
    def get_trending(limit: int = DEFAULT_PAGE_SIZE) -> List[Soundboard]:
        """
        Calculate and retrieve trending soundboards.

        Score is calculated as: (AvgRating * Count) + (CreatorFollowers * 2).

        Args:
            limit (int, optional): The maximum number of soundboards to return. Defaults to DEFAULT_PAGE_SIZE.

        Returns:
            list[Soundboard]: A list of trending Soundboard objects.
        """
        db_sb = get_soundboards_db()
        db_ac = get_accounts_db()

        # We perform a joined score calculation
        # 1. Get rating stats
        cur_sb = db_sb.cursor()
        cur_sb.execute(
            """
            SELECT s.id, AVG(r.score) as avg_score, COUNT(r.id) as rating_count
            FROM soundboards s
            LEFT JOIN ratings r ON s.id = r.soundboard_id
            WHERE s.is_public = 1
            GROUP BY s.id
        """
        )
        sb_stats = {
            row["id"]: (row["avg_score"] or 0, row["rating_count"])
            for row in cur_sb.fetchall()
        }

        # 2. Get all public boards to build full list
        all_public = Soundboard.get_public(order_by="recent")

        # 3. Calculate scores
        scored_boards = []
        for sb in all_public:
            avg, count = sb_stats.get(sb.id, (0, 0))

            # Fetch creator followers from accounts DB
            cur_ac = db_ac.cursor()
            cur_ac.execute(
                "SELECT COUNT(*) FROM follows WHERE followed_id = ?", (sb.user_id,)
            )
            followers = cur_ac.fetchone()[0]

            # Weighted Score Formula
            score = (avg * count) + (followers * 2)
            scored_boards.append((sb, score))

        # Sort by score descending
        scored_boards.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored_boards[:limit]]

    @staticmethod
    def get_featured() -> Optional[Soundboard]:
        """
        Retrieve the featured soundboard.

        Falls back to the top trending board if no featured board is set.

        Returns:
            Soundboard or None: The featured Soundboard object.
        """
        from app.models.admin import AdminSettings

        featured_id = AdminSettings.get_setting("featured_soundboard_id")
        if featured_id:
            sb = Soundboard.get_by_id(featured_id)
            if sb and sb.is_public:
                return sb

        # Fallback to most trending public board
        trending = Soundboard.get_trending(limit=1)
        return trending[0] if trending else None

    @staticmethod
    def search(query: str, order_by: str = "recent") -> List[Soundboard]:
        """
        Search for soundboards by name, user, sound name, or tag.

        Args:
            query (str): The search query.
            order_by (str, optional): Sorting criteria. Defaults to "recent".

        Returns:
            list[Soundboard]: A list of matching Soundboard objects.
        """
        user_ids = []
        accounts_db = get_accounts_db()
        ac_cur = accounts_db.cursor()
        ac_cur.execute("SELECT id FROM users WHERE username LIKE ?", (f"%{query}%",))
        user_ids = [row["id"] for row in ac_cur.fetchall()]

        soundboards_db = get_soundboards_db()
        sb_cur = soundboards_db.cursor()

        # Build query for soundboards
        search_query = "SELECT DISTINCT id, name, user_id, icon, is_public, theme_color, theme_preset FROM soundboards WHERE is_public = 1 AND (name LIKE ?"
        params = [f"%{query}%"]

        if user_ids:
            placeholders = ",".join(["?"] * len(user_ids))
            search_query += f" OR user_id IN ({placeholders})"
            params.extend(user_ids)

        sb_cur.execute(
            "SELECT DISTINCT soundboard_id FROM sounds WHERE name LIKE ?",
            (f"%{query}%",),
        )
        sound_sb_ids = [row["soundboard_id"] for row in sb_cur.fetchall()]

        if sound_sb_ids:
            placeholders = ",".join(["?"] * len(sound_sb_ids))
            search_query += f" OR id IN ({placeholders})"
            params.extend(sound_sb_ids)

        # Search tags and get their board IDs
        sb_cur.execute(
            """
            SELECT DISTINCT soundboard_id FROM soundboard_tags st
            JOIN tags t ON st.tag_id = t.id
            WHERE t.name LIKE ?
        """,
            (f"%{query}%",),
        )
        tag_sb_ids = [row["soundboard_id"] for row in sb_cur.fetchall()]

        if tag_sb_ids:
            placeholders = ",".join(["?"] * len(tag_sb_ids))
            search_query += f" OR id IN ({placeholders})"
            params.extend(tag_sb_ids)

        search_query += ")"

        if order_by == "top":
            # Join with ratings for search
            final_query = f"""
                SELECT results.*, AVG(r.score) as avg_score
                FROM ({search_query}) as results
                LEFT JOIN ratings r ON results.id = r.soundboard_id
                GROUP BY results.id
                ORDER BY avg_score DESC, results.name ASC
            """
            sb_cur.execute(final_query, params)
        elif order_by == "name":
            search_query += " ORDER BY name ASC"
            sb_cur.execute(search_query, params)
        else:  # recent
            search_query += " ORDER BY created_at DESC, id DESC"
            sb_cur.execute(search_query, params)

        rows = sb_cur.fetchall()
        return [
            Soundboard(
                id=row["id"],
                name=row["name"],
                user_id=row["user_id"],
                icon=row["icon"],
                is_public=row["is_public"],
                theme_color=row["theme_color"],
                theme_preset=row["theme_preset"],
            )
            for row in rows
        ]

    def get_sounds(self) -> List[Sound]:
        """
        Retrieve all sounds associated with this soundboard.

        Returns:
            list[Sound]: A list of Sound objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM sounds WHERE soundboard_id = ? ORDER BY display_order ASC, name ASC",
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
                hotkey=row["hotkey"],
                bitrate=row["bitrate"],
                file_size=row["file_size"],
                format=row["format"],
            )
            for row in rows
        ]

    def get_creator_username(self) -> str:
        """
        Retrieve the username of the soundboard's creator.

        Returns:
            str: The username.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
        row = cur.fetchone()
        return str(row["username"]) if row else "Unknown"

    def get_average_rating(self) -> Dict[str, Union[float, int]]:
        """
        Calculate the average rating for the soundboard.

        Returns:
            dict: A dictionary containing 'average' (float) and 'count' (int).
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT AVG(score) as avg, COUNT(*) as count FROM ratings WHERE soundboard_id = ?",
            (self.id,),
        )
        row = cur.fetchone()
        return {
            "average": round(row["avg"], 1) if row["avg"] else 0,
            "count": row["count"],
        }

    def get_user_rating(self, user_id: int) -> int:
        """
        Retrieve the rating given by a specific user.

        Args:
            user_id (int): The user ID.

        Returns:
            int: The rating score, or 0 if not rated.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT score FROM ratings WHERE soundboard_id = ? AND user_id = ?",
            (self.id, user_id),
        )
        row = cur.fetchone()
        return int(row["score"]) if row else 0

    def get_comments(self) -> List[Comment]:
        """
        Retrieve all comments on the soundboard.

        Returns:
            list[Comment]: A list of Comment objects.
        """
        from app.models.social import Comment

        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM comments WHERE soundboard_id = ? ORDER BY created_at DESC",
            (self.id,),
        )
        rows = cur.fetchall()
        return [
            Comment(
                id=row["id"],
                user_id=row["user_id"],
                soundboard_id=row["soundboard_id"],
                text=row["text"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_tags(self) -> List[Tag]:
        """
        Retrieve all tags associated with the soundboard.

        Returns:
            list[Tag]: A list of Tag objects.
        """
        from app.models.social import Tag

        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            """
            SELECT t.* FROM tags t
            JOIN soundboard_tags st ON t.id = st.tag_id
            WHERE st.soundboard_id = ?
            ORDER BY t.name ASC
        """,
            (self.id,),
        )
        rows = cur.fetchall()
        return [Tag(id=row["id"], name=row["name"]) for row in rows]

    def get_collaborators(self) -> List[BoardCollaborator]:
        """
        Retrieve all collaborators for the soundboard.

        Returns:
            list[BoardCollaborator]: A list of BoardCollaborator objects.
        """
        from app.models.social import BoardCollaborator

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

    def add_tag(self, tag_name: str) -> None:
        """
        Add a tag to the soundboard.

        Creates the tag if it doesn't exist.

        Args:
            tag_name (str): The name of the tag.
        """
        from app.models.social import Tag

        db = get_soundboards_db()
        tag = Tag.get_or_create(tag_name)
        if not tag:
            return
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO soundboard_tags (soundboard_id, tag_id) VALUES (?, ?)",
            (self.id, tag.id),
        )
        db.commit()

    def remove_tag(self, tag_name: str) -> None:
        """
        Remove a tag from the soundboard.

        Args:
            tag_name (str): The name of the tag to remove.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            """
            DELETE FROM soundboard_tags
            WHERE soundboard_id = ? AND tag_id IN (SELECT id FROM tags WHERE name = ?)
        """,
            (self.id, tag_name.lower().strip()),
        )
        db.commit()

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
    ):
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
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            if self.display_order == 0:
                cur.execute(
                    "SELECT MAX(display_order) FROM sounds WHERE soundboard_id = ?",
                    (self.soundboard_id,),
                )
                max_row = cur.fetchone()
                max_order = max_row[0] if max_row and max_row[0] is not None else 0
                self.display_order = max_order + 1

            cur.execute(
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
            self.id = cur.lastrowid
        else:
            cur.execute(
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
        db.commit()

    def delete(self) -> None:
        """Delete the sound and its associated files from the filesystem."""
        if self.id:
            import os

            from flask import current_app

            db = get_soundboards_db()
            cur = db.cursor()

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

            cur.execute("DELETE FROM sounds WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(sound_id: int) -> Optional[Sound]:
        """
        Retrieve a sound by its ID.

        Args:
            sound_id (int): The ID of the sound.

        Returns:
            Sound or None: The Sound object if found, else None.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM sounds WHERE id = ?", (sound_id,))
        row = cur.fetchone()
        if row:
            return Sound(
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
        return None

    def __repr__(self) -> str:
        return f"<Sound {self.name}>"
