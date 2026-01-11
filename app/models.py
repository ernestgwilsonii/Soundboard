"""Data models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_accounts_db, get_soundboards_db
from app.enums import UserRole, Visibility


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
    ):
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
        db = get_accounts_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
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
            self.id = cur.lastrowid
        else:
            cur.execute(
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
        db.commit()

    def delete(self) -> None:
        """Permanently deletes the user and all associated data."""
        if not self.id:
            return

        db_ac = get_accounts_db()
        db_sb = get_soundboards_db()

        # 1. Delete Soundboards (this handles sounds and files via Soundboard.delete)
        sbs = Soundboard.get_by_user_id(self.id)
        for sb in sbs:
            sb.delete()

        # 2. Delete Playlists
        pls = Playlist.get_by_user_id(self.id)
        for pl in pls:
            pl.delete()

        # 3. Cleanup social records
        db_sb.execute("DELETE FROM ratings WHERE user_id = ?", (self.id,))
        db_sb.execute("DELETE FROM comments WHERE user_id = ?", (self.id,))
        db_sb.execute("DELETE FROM activities WHERE user_id = ?", (self.id,))
        db_sb.commit()

        # 4. Cleanup account records
        db_ac.execute("DELETE FROM favorites WHERE user_id = ?", (self.id,))
        db_ac.execute("DELETE FROM notifications WHERE user_id = ?", (self.id,))
        db_ac.execute("DELETE FROM users WHERE id = ?", (self.id,))
        db_ac.commit()

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
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO favorites (user_id, soundboard_id) VALUES (?, ?)",
            (self.id, soundboard_id),
        )
        db.commit()

    def remove_favorite(self, soundboard_id: int) -> None:
        """
        Remove a soundboard from the user's favorites.

        Args:
            soundboard_id (int): The ID of the soundboard to unfavorite.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "DELETE FROM favorites WHERE user_id = ? AND soundboard_id = ?",
            (self.id, soundboard_id),
        )
        db.commit()

    def get_favorites(self) -> List[int]:
        """
        Retrieve a list of the user's favorite soundboard IDs.

        Returns:
            list[int]: A list of soundboard IDs.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT soundboard_id FROM favorites WHERE user_id = ?", (self.id,))
        rows = cur.fetchall()
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

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User or None: The User object if found, else None.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            return User(
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
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            return User(
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
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return User(
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
        return None

    @staticmethod
    def get_all(
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "newest",
        search_query: Optional[str] = None,
    ) -> List[User]:
        """
        Retrieve a list of users with pagination, sorting, and search.

        Args:
            limit (int, optional): Maximum number of users to return. Defaults to 10.
            offset (int, optional): Number of users to skip. Defaults to 0.
            sort_by (str, optional): Sorting criteria ('newest', 'oldest', 'alpha', 'popular'). Defaults to "newest".
            search_query (str, optional): Search string for username.

        Returns:
            list[User]: A list of User objects.
        """
        db = get_accounts_db()
        cur = db.cursor()

        sql = "SELECT * FROM users WHERE 1=1"
        params: List[Any] = []

        if search_query:
            sql += " AND username LIKE ?"
            params.append(f"%{search_query}%")

        if sort_by == "popular":
            # This is complex because follows table is in accounts DB now (correct)
            # We can join with a subquery of follow counts
            sql = f"""
                SELECT u.*, COUNT(f.follower_id) as follower_count
                FROM ({sql}) u
                LEFT JOIN follows f ON u.id = f.followed_id
                GROUP BY u.id
                ORDER BY follower_count DESC, u.username ASC
            """
        elif sort_by == "oldest":
            sql += " ORDER BY created_at ASC"
        elif sort_by == "alpha":
            sql += " ORDER BY username ASC"
        else:  # newest
            sql += " ORDER BY created_at DESC"

        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur.execute(sql, params)
        rows = cur.fetchall()
        return [
            User(
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
            for row in rows
        ]

    @staticmethod
    def count_all(search_query: Optional[str] = None) -> int:
        """
        Count the total number of users matching a search query.

        Args:
            search_query (str, optional): Search string for username.

        Returns:
            int: The total count of users.
        """
        db = get_accounts_db()
        cur = db.cursor()
        sql = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []
        if search_query:
            sql += " AND username LIKE ?"
            params.append(f"%{search_query}%")
        cur.execute(sql, params)
        return int(cur.fetchone()[0])

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
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps(self.email, salt=salt)

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
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            email = s.loads(token, salt=salt, max_age=expiration)
        except Exception:
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
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (self.id, user_id),
        )
        db.commit()

    def unfollow(self, user_id: int) -> None:
        """
        Unfollow another user.

        Args:
            user_id (int): The ID of the user to unfollow.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
            (self.id, user_id),
        )
        db.commit()

    def is_following(self, user_id: int) -> bool:
        """
        Check if currently following another user.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if following, False otherwise.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
            (self.id, user_id),
        )
        return cur.fetchone() is not None

    def get_followers(self) -> List[User]:
        """
        Retrieve a list of followers.

        Returns:
            list[User]: List of User objects who follow this user.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            """
            SELECT u.* FROM users u
            JOIN follows f ON u.id = f.follower_id
            WHERE f.followed_id = ?
            ORDER BY u.username ASC
        """,
            (self.id,),
        )
        rows = cur.fetchall()
        return [
            User(
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
            for row in rows
        ]

    def get_following(self) -> List[User]:
        """
        Retrieve a list of users being followed.

        Returns:
            list[User]: List of User objects this user follows.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            """
            SELECT u.* FROM users u
            JOIN follows f ON u.id = f.followed_id
            WHERE f.follower_id = ?
            ORDER BY u.username ASC
        """,
            (self.id,),
        )
        rows = cur.fetchall()
        return [
            User(
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
            for row in rows
        ]

    def get_follower_count(self) -> int:
        """
        Get the number of followers.

        Returns:
            int: Count of followers.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM follows WHERE followed_id = ?", (self.id,))
        return int(cur.fetchone()[0])

    def get_following_count(self) -> int:
        """
        Get the number of users followed.

        Returns:
            int: Count of users followed.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ?", (self.id,))
        return int(cur.fetchone()[0])


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
    def get_trending(limit: int = 10) -> List[Soundboard]:
        """
        Calculate and retrieve trending soundboards.

        Score is calculated as: (AvgRating * Count) + (CreatorFollowers * 2).

        Args:
            limit (int, optional): The maximum number of soundboards to return. Defaults to 10.

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
        from app.db import get_accounts_db, get_soundboards_db

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

    def get_author(self) -> Optional[User]:
        """
        Retrieve the User object of the comment author.

        Returns:
            User or None: The User object.
        """
        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)


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

    def get_sounds(self) -> List[Sound]:
        """
        Retrieve all sounds in the playlist.

        Returns:
            list[Sound]: A list of Sound objects.
        """
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
    def get_popular(limit: int = 10) -> List[Tag]:
        """
        Retrieve the most popular tags based on usage.

        Args:
            limit (int, optional): Maximum number of tags. Defaults to 10.

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
    def get_recent(limit: int = 20) -> List[Activity]:
        """
        Retrieve recent activities.

        Args:
            limit (int, optional): Maximum number of activities. Defaults to 20.

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

    def get_user(self) -> Optional[User]:
        """
        Retrieve the user associated with this activity.

        Returns:
            User or None: The User object.
        """
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


class AdminSettings:
    """Manages global application settings stored in the database."""

    @staticmethod
    def get_setting(key: str, default: Any = None) -> Any:
        """
        Retrieve a setting value by key.

        Args:
            key (str): The setting key.
            default (any, optional): Default value if key not found.

        Returns:
            any: The setting value or default.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return row["value"]
        return default

    @staticmethod
    def set_setting(key: str, value: Any) -> None:
        """
        Set or update a setting value.

        Args:
            key (str): The setting key.
            value (any): The value to store.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO admin_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
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

    def get_user(self) -> Optional[User]:
        """
        Retrieve the User object for this collaborator.

        Returns:
            User or None: The User object.
        """
        if self.user_id is None:
            return None
        return User.get_by_id(self.user_id)
