DROP TABLE IF EXISTS soundboards;
DROP TABLE IF EXISTS sounds;

CREATE TABLE soundboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    icon TEXT,
    is_public INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    soundboard_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    icon TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    volume FLOAT NOT NULL DEFAULT 1.0,
    is_loop INTEGER NOT NULL DEFAULT 0,
    start_time FLOAT NOT NULL DEFAULT 0.0,
    end_time FLOAT,
    hotkey TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (soundboard_id) REFERENCES soundboards (id)
);

CREATE TABLE ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    soundboard_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, soundboard_id),
    FOREIGN KEY (soundboard_id) REFERENCES soundboards (id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    soundboard_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (soundboard_id) REFERENCES soundboards (id)
);

CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_public INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE playlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    sound_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (playlist_id) REFERENCES playlists (id),
    FOREIGN KEY (sound_id) REFERENCES sounds (id)
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE soundboard_tags (
    soundboard_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (soundboard_id, tag_id),
    FOREIGN KEY (soundboard_id) REFERENCES soundboards (id),
    FOREIGN KEY (tag_id) REFERENCES tags (id)
);

CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
