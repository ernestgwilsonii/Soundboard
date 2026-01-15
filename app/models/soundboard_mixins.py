"""Mixins for decomposing the Soundboard model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from app.models.social import Comment, Tag
    from .soundboard import Soundboard

from app.constants import DEFAULT_PAGE_SIZE
from app.db import get_accounts_db, get_soundboards_db


class SoundboardSocialMixin:
    """Handles social interactions like ratings, comments, and tagging."""

    id: Any

    def get_average_rating(self) -> Dict[str, Union[float, int]]:
        """Calculate average rating."""
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT AVG(score) as avg, COUNT(*) as count FROM ratings WHERE soundboard_id = ?",
            (self.id,),
        )
        row = database_cursor.fetchone()
        return {
            "average": round(row["avg"], 1) if row and row["avg"] else 0,
            "count": row["count"] if row else 0,
        }

    def get_user_rating(self, user_id: int) -> int:
        """Get rating for a specific user."""
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT score FROM ratings WHERE soundboard_id = ? AND user_id = ?",
            (self.id, user_id),
        )
        row = database_cursor.fetchone()
        return int(row["score"]) if row else 0

    def get_comments(self) -> List["Comment"]:
        """Get all comments."""
        from .social import Comment

        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT * FROM comments WHERE soundboard_id = ? ORDER BY created_at DESC",
            (self.id,),
        )
        rows = database_cursor.fetchall()
        return [Comment._from_row(row) for row in rows]

    def get_tags(self) -> List["Tag"]:
        """Get all tags."""
        from .social import Tag

        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            """
            SELECT tags.* FROM tags tags
            JOIN soundboard_tags soundboard_tags ON tags.id = soundboard_tags.tag_id
            WHERE soundboard_tags.soundboard_id = ?
            ORDER BY tags.name ASC
        """,
            (self.id,),
        )
        rows = database_cursor.fetchall()
        return [Tag(id=row["id"], name=row["name"]) for row in rows]

    def add_tag(self, tag_name: str) -> None:
        """Add a tag."""
        from .social import Tag

        tag = Tag.get_or_create(tag_name)
        if not tag:
            return
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "INSERT OR IGNORE INTO soundboard_tags (soundboard_id, tag_id) VALUES (?, ?)",
            (self.id, tag.id),
        )
        database_connection.commit()

    def remove_tag(self, tag_name: str) -> None:
        """Remove a tag."""
        database_connection = get_soundboards_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            """
            DELETE FROM soundboard_tags
            WHERE soundboard_id = ? AND tag_id IN (SELECT id FROM tags WHERE name = ?)
        """,
            (self.id, tag_name.lower().strip()),
        )
        database_connection.commit()


class SoundboardDiscoveryMixin:
    """Handles search, trending, and featured board discovery."""

    @staticmethod
    def get_trending(limit: int = DEFAULT_PAGE_SIZE) -> List[Soundboard]:
        """Get trending boards."""
        import app.models.soundboard as sb_models

        database_connection_soundboards = get_soundboards_db()
        database_connection_accounts = get_accounts_db()

        database_cursor_soundboards = database_connection_soundboards.cursor()
        database_cursor_soundboards.execute(
            """
            SELECT soundboard.id, AVG(rating.score) as avg_score, COUNT(rating.id) as rating_count
            FROM soundboards soundboard
            LEFT JOIN ratings rating ON soundboard.id = rating.soundboard_id
            WHERE soundboard.is_public = 1
            GROUP BY soundboard.id
        """
        )
        soundboard_stats = {
            row["id"]: (row["avg_score"] or 0, row["rating_count"])
            for row in database_cursor_soundboards.fetchall()
        }

        all_public_soundboards = sb_models.Soundboard.get_public(order_by="recent")
        scored_soundboards = []
        for soundboard in all_public_soundboards:
            avg_rating, rating_count = soundboard_stats.get(soundboard.id, (0, 0))
            database_cursor_accounts = database_connection_accounts.cursor()
            database_cursor_accounts.execute(
                "SELECT COUNT(*) FROM follows WHERE followed_id = ?",
                (soundboard.user_id,),
            )
            result = database_cursor_accounts.fetchone()
            follower_count = result[0] if result else 0
            score = (avg_rating * rating_count) + (follower_count * 2)
            scored_soundboards.append((soundboard, score))

        scored_soundboards.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored_soundboards[:limit]]

    @staticmethod
    def get_featured() -> Optional[Soundboard]:
        """Get featured board."""
        import app.models.soundboard as sb_models
        from app.models.admin import AdminSettings

        featured_id_string = AdminSettings.get_setting("featured_soundboard_id")
        if featured_id_string:
            featured_soundboard = sb_models.Soundboard.get_by_id(
                int(featured_id_string)
            )
            if featured_soundboard and featured_soundboard.is_public:
                return featured_soundboard

        trending_soundboards = SoundboardDiscoveryMixin.get_trending(limit=1)
        return trending_soundboards[0] if trending_soundboards else None

    @staticmethod
    def search(query_string: str, order_by: str = "recent") -> List[Soundboard]:
        """Search boards."""
        import app.models.soundboard as sb_models

        user_ids = []
        database_connection_accounts = get_accounts_db()
        database_cursor_accounts = database_connection_accounts.cursor()
        database_cursor_accounts.execute(
            "SELECT id FROM users WHERE username LIKE ?", (f"%{query_string}%",)
        )
        user_ids = [row["id"] for row in database_cursor_accounts.fetchall()]

        database_connection_soundboards = get_soundboards_db()
        database_cursor_soundboards = database_connection_soundboards.cursor()

        sql_query = "SELECT DISTINCT id, name, user_id, icon, is_public, theme_color, theme_preset FROM soundboards WHERE is_public = 1 AND (name LIKE ?"
        query_parameters = [f"%{query_string}%"]

        if user_ids:
            placeholders = ",".join(["?"] * len(user_ids))
            sql_query += f" OR user_id IN ({placeholders})"
            query_parameters.extend(user_ids)

        database_cursor_soundboards.execute(
            "SELECT DISTINCT soundboard_id FROM sounds WHERE name LIKE ?",
            (f"%{query_string}%",),
        )
        ids_from_sounds = [
            row["soundboard_id"] for row in database_cursor_soundboards.fetchall()
        ]

        if ids_from_sounds:
            placeholders = ",".join(["?"] * len(ids_from_sounds))
            sql_query += f" OR id IN ({placeholders})"
            query_parameters.extend(ids_from_sounds)

        database_cursor_soundboards.execute(
            """
            SELECT DISTINCT soundboard_id FROM soundboard_tags soundboard_tags
            JOIN tags tags ON soundboard_tags.tag_id = tags.id
            WHERE tags.name LIKE ?
        """,
            (f"%{query_string}%",),
        )
        ids_from_tags = [
            row["soundboard_id"] for row in database_cursor_soundboards.fetchall()
        ]

        if ids_from_tags:
            placeholders = ",".join(["?"] * len(ids_from_tags))
            sql_query += f" OR id IN ({placeholders})"
            query_parameters.extend(ids_from_tags)

        sql_query += ")"

        if order_by == "top":
            final_query = f"""
                SELECT results.*, AVG(ratings.score) as avg_score
                FROM ({sql_query}) as results
                LEFT JOIN ratings ratings ON results.id = ratings.soundboard_id
                GROUP BY results.id
                ORDER BY avg_score DESC, results.name ASC
            """
            database_cursor_soundboards.execute(final_query, query_parameters)
        elif order_by == "name":
            sql_query += " ORDER BY name ASC"
            database_cursor_soundboards.execute(sql_query, query_parameters)
        else:  # recent
            sql_query += " ORDER BY created_at DESC, id DESC"
            database_cursor_soundboards.execute(sql_query, query_parameters)

        rows = database_cursor_soundboards.fetchall()
        return [sb_models.Soundboard._from_row(row) for row in rows]
