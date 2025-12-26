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
    """),
    (9, 'create_playlists_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            is_public INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """),
    (10, 'create_playlist_items_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS playlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            sound_id INTEGER NOT NULL,
            display_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (playlist_id) REFERENCES playlists (id),
            FOREIGN KEY (sound_id) REFERENCES sounds (id)
        );
    """),
    (11, 'create_tags_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """),
    (12, 'create_soundboard_tags_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS soundboard_tags (
            soundboard_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (soundboard_id, tag_id),
            FOREIGN KEY (soundboard_id) REFERENCES soundboards (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        );
    """),
    (13, 'add_avatar_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN avatar_path TEXT;
    """),
    (14, 'add_hotkey_to_sounds', Config.SOUNDBOARDS_DB, """
        ALTER TABLE sounds ADD COLUMN hotkey TEXT;
    """),
    (15, 'create_activities_table', Config.SOUNDBOARDS_DB, """
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """),
    (16, 'add_lockout_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
    """),
    (17, 'add_lockout_until_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN lockout_until TIMESTAMP;
    """),
    (18, 'add_profile_fields_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN bio TEXT;
    """),
    (19, 'add_social_x_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN social_x TEXT;
    """),
    (20, 'add_social_youtube_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN social_youtube TEXT;
    """),
    (21, 'add_social_website_to_users', Config.ACCOUNTS_DB, """
        ALTER TABLE users ADD COLUMN social_website TEXT;
    """),
    (22, 'add_theme_color_to_soundboards', Config.SOUNDBOARDS_DB, """
        ALTER TABLE soundboards ADD COLUMN theme_color TEXT DEFAULT '#0d6efd';
    """),
    (23, 'create_notifications_table', Config.ACCOUNTS_DB, """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """),
    (24, 'add_theme_preset_to_soundboards', Config.SOUNDBOARDS_DB, """
        ALTER TABLE soundboards ADD COLUMN theme_preset TEXT DEFAULT 'default';
    """),
    (25, 'create_follows_table', Config.ACCOUNTS_DB, """
        CREATE TABLE IF NOT EXISTS follows (
            follower_id INTEGER NOT NULL,
            followed_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (follower_id, followed_id),
            FOREIGN KEY (follower_id) REFERENCES users (id),
            FOREIGN KEY (followed_id) REFERENCES users (id)
        );
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
