"""User model."""

from __future__ import annotations

from typing import Any, List, Optional

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.constants import DEFAULT_PAGE_SIZE
from app.db import get_accounts_db, get_soundboards_db
from app.enums import UserRole


class User(UserMixin):
    """
    Represents a user in the system.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): The user's username.
        email (str): The user's email address.
        password_hash (str): Hashed password.
        role (UserRole): User role (e.g., ADMIN, USER).
        active (bool): Whether the account is active.
        is_verified (bool): Whether the email is verified.
        avatar_path (str): Path to the user's avatar image.
        failed_login_attempts (int): Count of consecutive failed logins.
        lockout_until (str): Timestamp until which the account is locked.
        bio (str): User biography.
        social_x (str): X (Twitter) profile URL.
        social_youtube (str): YouTube channel URL.
        social_website (str): Personal website URL.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password_hash: Optional[str] = None,
        role: UserRole = UserRole.USER,
        active: bool = True,
        is_verified: bool = False,
        avatar_path: Optional[str] = None,
        failed_login_attempts: int = 0,
        lockout_until: Optional[str] = None,
        bio: Optional[str] = None,
        social_x: Optional[str] = None,
        social_youtube: Optional[str] = None,
        social_website: Optional[str] = None,
    ) -> None:
        """
        Initialize a new User instance.

        Args:
            id (int, optional): User ID.
            username (str, optional): Username.
            email (str, optional): Email address.
            password_hash (str, optional): Hashed password.
            role (UserRole, optional): User role. Defaults to UserRole.USER.
            active (bool, optional): Is account active. Defaults to True.
            is_verified (bool, optional): Is email verified. Defaults to False.
            avatar_path (str, optional): Path to avatar.
            failed_login_attempts (int, optional): Failed login count. Defaults to 0.
            lockout_until (str, optional): Lockout timestamp.
            bio (str, optional): User bio.
            social_x (str, optional): X profile link.
            social_youtube (str, optional): YouTube profile link.
            social_website (str, optional): Website link.
        """
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.active = bool(active)
        self.is_verified = bool(is_verified)
        self.avatar_path = avatar_path
        self.failed_login_attempts = int(failed_login_attempts)
        self.lockout_until = lockout_until
        self.bio = bio
        self.social_x = social_x
        self.social_youtube = social_youtube
        self.social_website = social_website

    @property
    def is_active(self) -> bool:
        """Check if the user account is active."""
        return self.active

    @property
    def is_admin(self) -> bool:
        """Check if the user has admin privileges."""
        return self.role == UserRole.ADMIN

    def set_password(self, password: str) -> None:
        """
        Set the password for the user.

        Args:
            password (str): The plain text password to hash and store.
        """
        self.password_hash = generate_password_hash(password)

    def save(self) -> None:
        """
        Save the user to the database.

        Inserts a new record if id is None, otherwise updates the existing record.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        if self.id is None:
            database_cursor.execute(
                "INSERT INTO users (username, email, password_hash, role, active, is_verified, avatar_path, failed_login_attempts, lockout_until, bio, social_x, social_youtube, social_website) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.username,
                    self.email,
                    self.password_hash,
                    self.role,
                    int(self.active),
                    int(self.is_verified),
                    self.avatar_path,
                    self.failed_login_attempts,
                    self.lockout_until,
                    self.bio,
                    self.social_x,
                    self.social_youtube,
                    self.social_website,
                ),
            )
            self.id = database_cursor.lastrowid
        else:
            database_cursor.execute(
                "UPDATE users SET username=?, email=?, password_hash=?, role=?, active=?, is_verified=?, avatar_path=?, failed_login_attempts=?, lockout_until=?, bio=?, social_x=?, social_youtube=?, social_website=? WHERE id=?",
                (
                    self.username,
                    self.email,
                    self.password_hash,
                    self.role,
                    int(self.active),
                    int(self.is_verified),
                    self.avatar_path,
                    self.failed_login_attempts,
                    self.lockout_until,
                    self.bio,
                    self.social_x,
                    self.social_youtube,
                    self.social_website,
                    self.id,
                ),
            )
        database_connection.commit()

    def delete(self) -> None:
        """Permanently deletes the user and all associated data."""
        if not self.id:
            return

        from .playlist import Playlist
        from .soundboard import Soundboard

        database_connection_accounts = get_accounts_db()
        database_connection_soundboards = get_soundboards_db()

        # 1. Delete Soundboards (this handles sounds and files via Soundboard.delete)
        soundboards = Soundboard.get_by_user_id(self.id)
        for soundboard in soundboards:
            soundboard.delete()

        # 2. Delete Playlists
        playlists = Playlist.get_by_user_id(self.id)
        for playlist in playlists:
            playlist.delete()

        # 3. Cleanup social records
        database_connection_soundboards.execute(
            "DELETE FROM ratings WHERE user_id = ?", (self.id,)
        )
        database_connection_soundboards.execute(
            "DELETE FROM comments WHERE user_id = ?", (self.id,)
        )
        database_connection_soundboards.execute(
            "DELETE FROM activities WHERE user_id = ?", (self.id,)
        )
        database_connection_soundboards.commit()

        # 4. Cleanup account records
        database_connection_accounts.execute(
            "DELETE FROM favorites WHERE user_id = ?", (self.id,)
        )
        database_connection_accounts.execute(
            "DELETE FROM notifications WHERE user_id = ?", (self.id,)
        )
        database_connection_accounts.execute(
            "DELETE FROM users WHERE id = ?", (self.id,)
        )
        database_connection_accounts.commit()

        # 5. Delete avatar file if exists
        if self.avatar_path:
            import os

            from flask import current_app

            full_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], self.avatar_path
            )
            if os.path.exists(full_path):
                os.remove(full_path)

    def add_favorite(self, soundboard_id: int) -> None:
        """
        Add a soundboard to the user's favorites.

        Args:
            soundboard_id (int): The ID of the soundboard to favorite.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "INSERT OR IGNORE INTO favorites (user_id, soundboard_id) VALUES (?, ?)",
            (self.id, soundboard_id),
        )
        database_connection.commit()

    def remove_favorite(self, soundboard_id: int) -> None:
        """
        Remove a soundboard from the user's favorites.

        Args:
            soundboard_id (int): The ID of the soundboard to unfavorite.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND soundboard_id = ?",
            (self.id, soundboard_id),
        )
        database_connection.commit()

    def get_favorites(self) -> List[int]:
        """
        Retrieve a list of the user's favorite soundboard IDs.

        Returns:
            list[int]: A list of soundboard IDs.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT soundboard_id FROM favorites WHERE user_id = ?", (self.id,)
        )
        rows = database_cursor.fetchall()
        return [row["soundboard_id"] for row in rows]

    def check_password(self, password: str) -> bool:
        """
        Check if the provided password matches the user's password hash.

        Args:
            password (str): The password to check.

        Returns:
            bool: True if password matches, False otherwise.
        """
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    @classmethod
    def _from_row(cls, row: Any) -> User:
        """Helper to create a User instance from a database row."""
        return cls(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            active=row["active"],
            is_verified=row["is_verified"],
            avatar_path=row["avatar_path"],
            failed_login_attempts=row["failed_login_attempts"],
            lockout_until=row["lockout_until"],
            bio=row["bio"],
            social_x=row["social_x"],
            social_youtube=row["social_youtube"],
            social_website=row["social_website"],
        )

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User or None: The User object if found, else None.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = database_cursor.fetchone()
        if row:
            return User._from_row(row)
        return None

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User or None: The User object if found, else None.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = database_cursor.fetchone()
        if row:
            return User._from_row(row)
        return None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The user ID to search for.

        Returns:
            User or None: The User object if found, else None.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = database_cursor.fetchone()
        if row:
            return User._from_row(row)
        return None

    @staticmethod
    def exists_by_username(username: str) -> bool:
        """Check if a user with the given username exists."""
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return database_cursor.fetchone() is not None

    @staticmethod
    def exists_by_email(email: str) -> bool:
        """Check if a user with the given email exists."""
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        return database_cursor.fetchone() is not None

    @staticmethod
    def get_all(
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
        sort_by: str = "newest",
        search_query: Optional[str] = None,
    ) -> List[User]:
        """
        Retrieve a list of users with pagination, sorting, and search.

        Args:
            limit (int, optional): Maximum number of users to return. Defaults to DEFAULT_PAGE_SIZE.
            offset (int, optional): Number of users to skip. Defaults to 0.
            sort_by (str, optional): Sorting criteria ('newest', 'oldest', 'alpha', 'popular'). Defaults to "newest".
            search_query (str, optional): Search string for username.

        Returns:
            list[User]: A list of User objects.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()

        sql = "SELECT * FROM users WHERE 1=1"
        params: List[Any] = []

        if search_query:
            sql += " AND username LIKE ?"
            params.append(f"%{search_query}%")

        if sort_by == "popular":
            sql = f"""
                SELECT users.*, COUNT(follows.follower_id) as follower_count
                FROM ({sql}) users
                LEFT JOIN follows follows ON users.id = follows.followed_id
                GROUP BY users.id
                ORDER BY follower_count DESC, users.username ASC
            """
        elif sort_by == "oldest":
            sql += " ORDER BY created_at ASC"
        elif sort_by == "alpha":
            sql += " ORDER BY username ASC"
        else:  # newest
            sql += " ORDER BY created_at DESC"

        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        database_cursor.execute(sql, params)
        rows = database_cursor.fetchall()
        return [User._from_row(row) for row in rows]

    @staticmethod
    def count_all(search_query: Optional[str] = None) -> int:
        """
        Count the total number of users matching a search query.

        Args:
            search_query (str, optional): Search string for username.

        Returns:
            int: The total count of users.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        sql = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []
        if search_query:
            sql += " AND username LIKE ?"
            params.append(f"%{search_query}%")
        database_cursor.execute(sql, params)
        result = database_cursor.fetchone()
        return int(result[0]) if result else 0

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def get_token(self, salt: str) -> str:
        """
        Generate a secure token for the user.

        Args:
            salt (str): The salt to use for token generation.

        Returns:
            str: The generated token.
        """
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return serializer.dumps(self.email, salt=salt)

    @staticmethod
    def verify_token(token: str, salt: str, expiration: int = 3600) -> Optional[User]:
        """
        Verify a token and retrieve the associated user.

        Args:
            token (str): The token to verify.
            salt (str): The salt used for token generation.
            expiration (int, optional): Token expiration in seconds. Defaults to 3600.

        Returns:
            User or None: The User object if token is valid, else None.
        """
        from itsdangerous import BadSignature, SignatureExpired

        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            email = serializer.loads(token, salt=salt, max_age=expiration)
        except (BadSignature, SignatureExpired):
            return None
        return User.get_by_email(email)

    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock account if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import datetime, timedelta

            self.lockout_until = (datetime.now() + timedelta(minutes=15)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        self.save()

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts and clear lockout status."""
        self.failed_login_attempts = 0
        self.lockout_until = None
        self.save()

    def is_locked(self) -> bool:
        """
        Check if the account is currently locked out.

        Returns:
            bool: True if locked out, False otherwise.
        """
        if not self.lockout_until:
            return False
        from datetime import datetime

        lockout_time = datetime.strptime(self.lockout_until, "%Y-%m-%d %H:%M:%S")
        if datetime.now() > lockout_time:
            # Lock expired
            return False
        return True

    def follow(self, user_id: int) -> None:
        """
        Follow another user.

        Args:
            user_id (int): The ID of the user to follow.
        """
        if self.id == user_id:
            return
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (self.id, user_id),
        )
        database_connection.commit()

    def unfollow(self, user_id: int) -> None:
        """
        Unfollow another user.

        Args:
            user_id (int): The ID of the user to unfollow.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
            (self.id, user_id),
        )
        database_connection.commit()

    def is_following(self, user_id: int) -> bool:
        """
        Check if currently following another user.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if following, False otherwise.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
            (self.id, user_id),
        )
        return database_cursor.fetchone() is not None

    def get_followers(self) -> List[User]:
        """
        Retrieve a list of followers.

        Returns:
            list[User]: List of User objects who follow this user.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            """
            SELECT users.* FROM users users
            JOIN follows follows ON users.id = follows.follower_id
            WHERE follows.followed_id = ?
            ORDER BY users.username ASC
        """,
            (self.id,),
        )
        rows = database_cursor.fetchall()
        return [User._from_row(row) for row in rows]

    def get_following(self) -> List[User]:
        """
        Retrieve a list of users being followed.

        Returns:
            list[User]: List of User objects this user follows.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            """
            SELECT users.* FROM users users
            JOIN follows follows ON users.id = follows.followed_id
            WHERE follows.follower_id = ?
            ORDER BY users.username ASC
        """,
            (self.id,),
        )
        rows = database_cursor.fetchall()
        return [User._from_row(row) for row in rows]

    def get_follower_count(self) -> int:
        """
        Get the number of followers.

        Returns:
            int: Count of followers.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT COUNT(*) FROM follows WHERE followed_id = ?", (self.id,)
        )
        result = database_cursor.fetchone()
        return int(result[0]) if result else 0

    def get_following_count(self) -> int:
        """
        Get the number of users followed.

        Returns:
            int: Count of users followed.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT COUNT(*) FROM follows WHERE follower_id = ?", (self.id,)
        )
        result = database_cursor.fetchone()
        return int(result[0]) if result else 0
