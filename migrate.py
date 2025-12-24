import sqlite3
import os
import sys
from config import Config

# List of migrations to apply
# Format: (id, name, db_path, sql_command)
MIGRATIONS = [
    # Already applied manually in previous steps but added here for tracking
    (1, 'add_display_order_to_sounds', Config.SOUNDBOARDS_DB, "ALTER TABLE sounds ADD COLUMN display_order INTEGER NOT NULL DEFAULT 0;"),
    (2, 'create_ratings_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            soundboard_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, soundboard_id),
            FOREIGN KEY (soundboard_id) REFERENCES soundboards (id)
        );
    """),
    (3, 'create_comments_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            soundboard_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (soundboard_id) REFERENCES soundboards (id)
        );
    """),
    (4, 'add_playback_settings_to_sounds', Config.SOUNDBOARDS_DB, """
        ALTER TABLE sounds ADD COLUMN volume FLOAT NOT NULL DEFAULT 1.0;
    """),
    (5, 'add_loop_to_sounds', Config.SOUNDBOARDS_DB, """
        ALTER TABLE sounds ADD COLUMN is_loop INTEGER NOT NULL DEFAULT 0;
    """),
    (6, 'add_trimming_to_sounds', Config.SOUNDBOARDS_DB, """
        ALTER TABLE sounds ADD COLUMN start_time FLOAT NOT NULL DEFAULT 0.0;
    """),
    (7, 'add_end_time_to_sounds', Config.SOUNDBOARDS_DB, """
        ALTER TABLE sounds ADD COLUMN end_time FLOAT;
    """),
    (8, 'add_is_verified_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0;
    """)
]

def init_migration_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def run_migrations():
    # Use accounts DB to track migrations (centralized)
    accounts_conn = sqlite3.connect(Config.ACCOUNTS_DB)
    init_migration_table(accounts_conn)
    
    cur = accounts_conn.cursor()
    cur.execute("SELECT id FROM migrations")
    applied_ids = [row[0] for row in cur.fetchall()]
    
    for mid, name, db_path, sql in MIGRATIONS:
        if mid not in applied_ids:
            print(f"Applying migration {mid}: {name}...")
            try:
                # Execute on target DB
                target_conn = sqlite3.connect(db_path)
                target_conn.execute(sql)
                target_conn.commit()
                target_conn.close()
                
                # Record in migrations table
                cur.execute("INSERT INTO migrations (id, name) VALUES (?, ?)", (mid, name))
                accounts_conn.commit()
                print(f"Successfully applied {name}.")
            except sqlite3.OperationalError as e:
                # Handle cases where column/table might already exist from manual runs
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    print(f"Skipping {name} (already exists in schema). Recording as applied.")
                    cur.execute("INSERT INTO migrations (id, name) VALUES (?, ?)", (mid, name))
                    accounts_conn.commit()
                else:
                    print(f"Error applying migration {name}: {e}")
                    sys.exit(1)
            except Exception as e:
                print(f"Critical error applying migration {name}: {e}")
                sys.exit(1)
        else:
            print(f"Migration {mid} ({name}) already applied.")
            
    accounts_conn.close()

if __name__ == "__main__":
    run_migrations()
