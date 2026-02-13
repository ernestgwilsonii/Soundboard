"""User model."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, List, Optional, cast

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.constants import DEFAULT_PAGE_SIZE
from app.enums import UserRole
from app.extensions import db_orm as db
from app.models.base import BaseModel

# Association Tables
follows = db.Table(
    "follows",
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("created_at", db.DateTime, server_default=func.now()),
)

favorites = db.Table(
    "favorites",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("soundboard_id", db.Integer, primary_key=True),
    db.Column("created_at", db.DateTime, server_default=func.now()),
)


class User(BaseModel, UserMixin):
    """Represents a user in the system."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    google_id = db.Column(db.String(256), unique=True, nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    avatar_path = db.Column(db.String(256), nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.String(32), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    social_x = db.Column(db.String(256), nullable=True)
    social_youtube = db.Column(db.String(256), nullable=True)
    social_website = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    followed = db.relationship(
        "User",
        secondary=follows,
        primaryjoin=(follows.c.follower_id == id),
        secondaryjoin=(follows.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @property
    def is_active(self) -> bool:
        """Check if the user account is active."""
        return cast(bool, self.active if self.active is not None else True)

    @property
    def is_authenticated(self) -> bool:
        """User is authenticated."""
        return True

    @property
    def is_admin(self) -> bool:
        """Check if the user has admin privileges."""
        return cast(bool, self.role == UserRole.ADMIN)

    def set_password(self, password: str) -> None:
        """Set the password for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password hash."""
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def delete(self) -> None:
        """Permanently deletes the user and all associated data."""
        if not self.id:
            return

        from .playlist import Playlist
        from .soundboard import Soundboard

        # 1. Delete Soundboards (this handles sounds and files via Soundboard.delete)
        soundboards = Soundboard.get_by_user_id(self.id)
        for soundboard in soundboards:
            soundboard.delete()

        # 2. Delete Playlists
        playlists = Playlist.get_by_user_id(self.id)
        for playlist in playlists:
            playlist.delete()

        # 3. Cleanup social records in Soundboards DB
        from .social import Activity, Comment, Rating

        Rating.query.filter_by(user_id=self.id).delete()
        Comment.query.filter_by(user_id=self.id).delete()
        Activity.query.filter_by(user_id=self.id).delete()
        db.session.commit()

        # 4. Delete avatar file if exists
        if self.avatar_path:
            full_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], self.avatar_path
            )
            if os.path.exists(full_path):
                os.remove(full_path)

        # 5. Delete self (Cascade will handle follows/favorites if configured, but explicit is fine)
        super().delete()

    def add_favorite(self, soundboard_id: int) -> None:
        """Add a soundboard to the user's favorites."""
        stmt = favorites.insert().values(user_id=self.id, soundboard_id=soundboard_id)
        # Ignore conflicts (already exists)
        try:
            db.session.execute(stmt)
            db.session.commit()
        except Exception:
            db.session.rollback()

    def remove_favorite(self, soundboard_id: int) -> None:
        """Remove a soundboard from the user's favorites."""
        stmt = favorites.delete().where(
            (favorites.c.user_id == self.id)
            & (favorites.c.soundboard_id == soundboard_id)
        )
        db.session.execute(stmt)
        db.session.commit()

    def get_favorites(self) -> List[int]:
        """Retrieve a list of the user's favorite soundboard IDs."""
        stmt = db.select(favorites.c.soundboard_id).where(
            favorites.c.user_id == self.id
        )
        return [row[0] for row in db.session.execute(stmt)]

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Retrieve a user by their username."""
        return cast(Optional[User], User.query.filter_by(username=username).first())

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        return cast(Optional[User], User.query.filter_by(email=email).first())

    @staticmethod
    def exists_by_username(username: str) -> bool:
        """Check if a user with the given username exists."""
        return cast(bool, User.query.filter_by(username=username).first() is not None)

    @staticmethod
    def exists_by_email(email: str) -> bool:
        """Check if a user with the given email exists."""
        return cast(bool, User.query.filter_by(email=email).first() is not None)

    @staticmethod
    def get_all(
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
        sort_by: str = "newest",
        search_query: Optional[str] = None,
    ) -> List[User]:
        """Retrieve a list of users with pagination, sorting, and search."""
        query = User.query

        if search_query:
            query = query.filter(User.username.like(f"%{search_query}%"))

        if sort_by == "popular":
            # Sort by follower count
            # Use outerjoin to count followers
            subquery = (
                db.select(
                    follows.c.followed_id,
                    func.count(follows.c.follower_id).label("count"),
                )
                .group_by(follows.c.followed_id)
                .subquery()
            )

            query = query.outerjoin(subquery, User.id == subquery.c.followed_id)
            query = query.order_by(subquery.c.count.desc(), User.username.asc())
        elif sort_by == "oldest":
            query = query.order_by(User.created_at.asc())
        elif sort_by == "alpha":
            query = query.order_by(User.username.asc())
        else:  # newest
            query = query.order_by(User.created_at.desc())

        return cast(List[User], query.limit(limit).offset(offset).all())

    @staticmethod
    def count_all(search_query: Optional[str] = None) -> int:
        """Count the total number of users matching a search query."""
        query = User.query
        if search_query:
            query = query.filter(User.username.like(f"%{search_query}%"))
        return cast(int, query.count())

    def get_token(self, salt: str) -> str:
        """Generate a secure token for the user."""
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return serializer.dumps(self.email, salt=salt)

    @staticmethod
    def verify_token(token: str, salt: str, expiration: int = 3600) -> Optional[User]:
        """Verify a token and retrieve the associated user."""
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
            from datetime import timedelta

            # Store as string to match legacy format
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
        """Check if the account is currently locked out."""
        if not self.lockout_until:
            return False

        lockout_time = datetime.strptime(self.lockout_until, "%Y-%m-%d %H:%M:%S")
        if datetime.now() > lockout_time:
            return False
        return True

    def follow(self, user_id: int) -> None:
        """Follow another user."""
        if self.id == user_id:
            return
        user_to_follow = User.get_by_id(user_id)
        if user_to_follow:
            self.followed.append(user_to_follow)
            db.session.commit()

    def unfollow(self, user_id: int) -> None:
        """Unfollow another user."""
        user_to_unfollow = User.get_by_id(user_id)
        if user_to_unfollow:
            self.followed.remove(user_to_unfollow)
            db.session.commit()

    def is_following(self, user_id: int) -> bool:
        """Check if currently following another user."""
        return cast(
            bool, self.followed.filter(follows.c.followed_id == user_id).count() > 0
        )

    def get_followers(self) -> List[User]:
        """Retrieve a list of followers."""
        return cast(List[User], self.followers.all())

    def get_following(self) -> List[User]:
        """Retrieve a list of users being followed."""
        return cast(List[User], self.followed.all())

    def get_follower_count(self) -> int:
        """Get the number of followers."""
        return cast(int, self.followers.count())

    def get_following_count(self) -> int:
        """Get the number of users followed."""
        return cast(int, self.followed.count())

    def __repr__(self) -> str:
        return f"<User {self.username}>"
