DROP TABLE IF EXISTS users;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS admin_settings;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE favorites (
    user_id INTEGER NOT NULL,
    soundboard_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, soundboard_id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE admin_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO admin_settings (key, value) VALUES ('featured_soundboard_id', NULL);
