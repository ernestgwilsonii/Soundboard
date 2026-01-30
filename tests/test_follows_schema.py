from sqlalchemy import inspect

from app.extensions import db_orm as db


def test_follows_table_exists(app):
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"DEBUG: Found tables: {tables}")
        assert "follows" in tables, f"Table 'follows' should exist in {tables}"
