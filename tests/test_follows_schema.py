import sqlite3


def test_follows_table_exists(app):
    # Use the accounts DB from config
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"DEBUG: Found tables in {db_path}: {tables}")
    conn.close()

    assert "follows" in tables, f"Table 'follows' should exist in {tables}"
