"""Base model module."""

from typing import List, Optional, Type, TypeVar

from app.extensions import db_orm as db

T = TypeVar("T", bound="BaseModel")


class BaseModel(db.Model):  # type: ignore
    """Abstract base model.

    Provides Active Record style convenience methods wrapping SQLAlchemy sessions.
    """

    __abstract__ = True

    def save(self) -> None:
        """Save the current instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self) -> None:
        """Delete the current instance from the database."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls: Type[T], id: int) -> Optional[T]:
        """Fetch a record by its primary key."""
        return db.session.get(cls, id)

    @classmethod
    def get_all(cls: Type[T]) -> List[T]:
        """Fetch all records for this model."""
        return cls.query.all()
