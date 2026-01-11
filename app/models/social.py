"""Social interaction models."""

from __future__ import annotations

from typing import List, Optional

from app.constants import DEFAULT_PAGE_SIZE, LARGE_PAGE_SIZE
from app.db import get_accounts_db, get_soundboards_db


class Rating:
    """
    Represents a user's rating of a soundboard.

    Attributes:
        id (int): Unique identifier for the rating.
        user_id (int): ID of the user who rated.
        soundboard_id (int): ID of the soundboard being rated.
        score (int): The rating score (e.g., 1-5).
        created_at (str): Timestamp of creation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        soundboard_id: Optional[int] = None,
        score: int = 0,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.soundboard_id = soundboard_id
        self.score = score
        self.created_at = created_at

    def save(self) -> None:
        """
        Save the rating to the database.

        Updates the existing rating if the user has already rated this soundboard.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO ratings (user_id, soundboard_id, score) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, soundboard_id) DO UPDATE SET score=excluded.score",
                (self.user_id, self.soundboard_id, self.score),
            )
            self.id = cur.lastrowid
        else:
            cur.execute("UPDATE ratings SET score=? WHERE id=?", (self.score, self.id))
        db.commit()


class Comment:
    """
    Represents a comment on a soundboard.

    Attributes:
        id (int): Unique identifier for the comment.
        user_id (int): ID of the user who commented.
        soundboard_id (int): ID of the soundboard.
        text (str): The comment text.
        created_at (str): Timestamp of creation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        soundboard_id: Optional[int] = None,
        text: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.soundboard_id = soundboard_id
        self.text = text
        self.created_at = created_at

    def save(self) -> None:
        """Save the comment to the database."""
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO comments (user_id, soundboard_id, text) VALUES (?, ?, ?)",
                (self.user_id, self.soundboard_id, self.text),
            )
            self.id = cur.lastrowid
        else:
            cur.execute("UPDATE comments SET text=? WHERE id=?", (self.text, self.id))
        db.commit()

    def delete(self) -> None:
        """Delete the comment from the database."""
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            cur.execute("DELETE FROM comments WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(comment_id: int) -> Optional[Comment]:
        """
        Retrieve a comment by its ID.

        Args:
            comment_id (int): The comment ID.

        Returns:
            Comment or None: The Comment object if found.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        row = cur.fetchone()
        if row:
            return Comment(
                id=row["id"],
                user_id=row["user_id"],
                soundboard_id=row["soundboard_id"],
                text=row["text"],
                created_at=row["created_at"],
            )
        return None

    def get_author_username(self) -> str:
        """
        Retrieve the username of the comment author.

        Returns:
            str: The username.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
        row = cur.fetchone()
        return str(row["username"]) if row else "Unknown"

    def get_author(self) -> Optional:
        """
        Retrieve the User object of the comment author.

        Returns:
            User or None: The User object.
        """
        from app.models.user import User

        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)


class Tag:
    """
    Represents a tag for categorization.

    Attributes:
        id (int): Unique identifier.
        name (str): Tag name.
    """

    def __init__(self, id: Optional[int] = None, name: Optional[str] = None):
        self.id = id
        self.name = name

    @staticmethod
    def get_or_create(name: str) -> Optional[Tag]:
        """
        Retrieve a tag by name or create it if it doesn't exist.

        Args:
            name (str): The tag name.

        Returns:
            Tag or None: The Tag object.
        """
        name = name.lower().strip()
        if not name:
            return None
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM tags WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return Tag(id=row["id"], name=row["name"])

        cur.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        db.commit()
        return Tag(id=cur.lastrowid, name=name)

    @staticmethod
    def get_all() -> List[Tag]:
        """
        Retrieve all tags.

        Returns:
            list[Tag]: A list of Tag objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM tags ORDER BY name ASC")
        rows = cur.fetchall()
        return [Tag(id=row["id"], name=row["name"]) for row in rows]

    @staticmethod
    def get_popular(limit: int = DEFAULT_PAGE_SIZE) -> List[Tag]:
        """
        Retrieve the most popular tags based on usage.

        Args:
            limit (int, optional): Maximum number of tags. Defaults to DEFAULT_PAGE_SIZE.

        Returns:
            list[Tag]: A list of Tag objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            """
            SELECT t.*, COUNT(st.soundboard_id) as count
            FROM tags t
            JOIN soundboard_tags st ON t.id = st.tag_id
            GROUP BY t.id
            ORDER BY count DESC
            LIMIT ?
        """,
            (limit,),
        )
        rows = cur.fetchall()
        return [Tag(id=row["id"], name=row["name"]) for row in rows]


class Activity:
    """
    Represents a user activity record.

    Attributes:
        id (int): Unique identifier.
        user_id (int): ID of the user.
        action_type (str): Type of action (e.g., 'upload', 'comment').
        description (str): Description of the activity.
        created_at (str): Timestamp of creation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        description: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.action_type = action_type
        self.description = description
        self.created_at = created_at

    @staticmethod
    def record(user_id: int, action_type: str, description: str) -> None:
        """
        Record a new user activity.

        Args:
            user_id (int): The user ID.
            action_type (str): The type of action.
            description (str): Activity description.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO activities (user_id, action_type, description) VALUES (?, ?, ?)",
            (user_id, action_type, description),
        )
        db.commit()

    @staticmethod
    def get_recent(limit: int = LARGE_PAGE_SIZE) -> List[Activity]:
        """
        Retrieve recent activities.

        Args:
            limit (int, optional): Maximum number of activities. Defaults to LARGE_PAGE_SIZE.

        Returns:
            list[Activity]: A list of Activity objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM activities ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        return [
            Activity(
                id=row["id"],
                user_id=row["user_id"],
                action_type=row["action_type"],
                description=row["description"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_user(self) -> Optional:
        """
        Retrieve the user associated with this activity.

        Returns:
            User or None: The User object.
        """
        from app.models.user import User

        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)


class Notification:
    """
    Represents a user notification.

    Attributes:
        id (int): Unique identifier.
        user_id (int): ID of the recipient user.
        type (str): Notification type (e.g., 'system', 'social').
        message (str): Notification content.
        link (str): Optional URL link.
        is_read (bool): Whether the notification has been read.
        created_at (str): Timestamp of creation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        user_id: Optional[int] = None,
        type: Optional[str] = None,
        message: Optional[str] = None,
        link: Optional[str] = None,
        is_read: bool = False,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.message = message
        self.link = link
        self.is_read = bool(is_read)
        self.created_at = created_at

    @staticmethod
    def add(user_id: int, type: str, message: str, link: Optional[str] = None) -> None:
        """
        Create a new notification for a user.

        Args:
            user_id (int): Recipient user ID.
            type (str): Notification type.
            message (str): Notification text.
            link (str, optional): Action link.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO notifications (user_id, type, message, link) VALUES (?, ?, ?, ?)",
            (user_id, type, message, link),
        )
        db.commit()

    @staticmethod
    def get_unread_for_user(user_id: int) -> List[Notification]:
        """
        Retrieve all unread notifications for a user.

        Args:
            user_id (int): The user ID.

        Returns:
            list[Notification]: A list of Notification objects.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        return [
            Notification(
                id=row["id"],
                user_id=row["user_id"],
                type=row["type"],
                message=row["message"],
                link=row["link"],
                is_read=row["is_read"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def mark_all_read(user_id: int) -> None:
        """
        Mark all notifications as read for a user.

        Args:
            user_id (int): The user ID.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,)
        )
        db.commit()


class BoardCollaborator:
    """
    Represents a collaborator on a soundboard.

    Attributes:
        id (int): Unique identifier.
        soundboard_id (int): ID of the soundboard.
        user_id (int): ID of the collaborator user.
        role (str): Role of the collaborator (e.g., 'editor').
        created_at (str): Timestamp of creation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        soundboard_id: Optional[int] = None,
        user_id: Optional[int] = None,
        role: str = "editor",
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.soundboard_id = soundboard_id
        self.user_id = user_id
        self.role = role
        self.created_at = created_at

    def save(self) -> None:
        """Save the collaborator record to the database."""
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO board_collaborators (soundboard_id, user_id, role) VALUES (?, ?, ?)",
                (self.soundboard_id, self.user_id, self.role),
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE board_collaborators SET role=? WHERE id=?", (self.role, self.id)
            )
        db.commit()

    def delete(self) -> None:
        """Remove the collaborator."""
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            cur.execute("DELETE FROM board_collaborators WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_for_board(soundboard_id: int) -> List[BoardCollaborator]:
        """
        Retrieve all collaborators for a specific soundboard.

        Args:
            soundboard_id (int): The soundboard ID.

        Returns:
            list[BoardCollaborator]: A list of BoardCollaborator objects.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM board_collaborators WHERE soundboard_id = ?",
            (soundboard_id,),
        )
        rows = cur.fetchall()
        return [
            BoardCollaborator(
                id=row["id"],
                soundboard_id=row["soundboard_id"],
                user_id=row["user_id"],
                role=row["role"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def get_by_user_and_board(
        user_id: int, soundboard_id: int
    ) -> Optional[BoardCollaborator]:
        """
        Retrieve a specific collaborator record.

        Args:
            user_id (int): The user ID.
            soundboard_id (int): The soundboard ID.

        Returns:
            BoardCollaborator or None: The BoardCollaborator object if found.
        """
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM board_collaborators WHERE user_id = ? AND soundboard_id = ?",
            (user_id, soundboard_id),
        )
        row = cur.fetchone()
        if row:
            return BoardCollaborator(
                id=row["id"],
                soundboard_id=row["soundboard_id"],
                user_id=row["user_id"],
                role=row["role"],
                created_at=row["created_at"],
            )
        return None

    def get_user(self) -> Optional:
        """
        Retrieve the User object for this collaborator.

        Returns:
            User or None: The User object.
        """
        from app.models.user import User

        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)
