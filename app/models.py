from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password_hash=None, role='user'):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def save(self):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            if self.id is None:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (self.username, self.email, self.password_hash, self.role)
                )
                self.id = cur.lastrowid
            else:
                cur.execute(
                    "UPDATE users SET username=?, email=?, password_hash=?, role=? WHERE id=?",
                    (self.username, self.email, self.password_hash, self.role, self.id)
                )
            conn.commit()

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if row:
                return User(id=row['id'], username=row['username'], email=row['email'], 
                            password_hash=row['password_hash'], role=row['role'])
        return None

    @staticmethod
    def get_by_id(user_id):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                return User(id=row['id'], username=row['username'], email=row['email'], 
                            password_hash=row['password_hash'], role=row['role'])
        return None

    def __repr__(self):
        return f'<User {self.username}>'

class Soundboard:
    def __init__(self, id=None, name=None, user_id=None, icon=None):
        self.id = id
        self.name = name
        self.user_id = user_id
        self.icon = icon

    def save(self):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.SOUNDBOARDS_DB) as conn:
            cur = conn.cursor()
            if self.id is None:
                cur.execute(
                    "INSERT INTO soundboards (name, user_id, icon) VALUES (?, ?, ?)",
                    (self.name, self.user_id, self.icon)
                )
                self.id = cur.lastrowid
            else:
                cur.execute(
                    "UPDATE soundboards SET name=?, user_id=?, icon=? WHERE id=?",
                    (self.name, self.user_id, self.icon, self.id)
                )
            conn.commit()

    def delete(self):
        import sqlite3
        from config import Config
        if self.id:
            with sqlite3.connect(Config.SOUNDBOARDS_DB) as conn:
                cur = conn.cursor()
                # Also delete associated sounds
                cur.execute("DELETE FROM sounds WHERE soundboard_id = ?", (self.id,))
                cur.execute("DELETE FROM soundboards WHERE id = ?", (self.id,))
                conn.commit()

    @staticmethod
    def get_by_id(soundboard_id):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.SOUNDBOARDS_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM soundboards WHERE id = ?", (soundboard_id,))
            row = cur.fetchone()
            if row:
                return Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], icon=row['icon'])
        return None

    def __repr__(self):
        return f'<Soundboard {self.name}>'

class Sound:
    def __init__(self, id=None, soundboard_id=None, name=None, file_path=None, icon=None):
        self.id = id
        self.soundboard_id = soundboard_id
        self.name = name
        self.file_path = file_path
        self.icon = icon

    def save(self):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.SOUNDBOARDS_DB) as conn:
            cur = conn.cursor()
            if self.id is None:
                cur.execute(
                    "INSERT INTO sounds (soundboard_id, name, file_path, icon) VALUES (?, ?, ?, ?)",
                    (self.soundboard_id, self.name, self.file_path, self.icon)
                )
                self.id = cur.lastrowid
            else:
                cur.execute(
                    "UPDATE sounds SET soundboard_id=?, name=?, file_path=?, icon=? WHERE id=?",
                    (self.soundboard_id, self.name, self.file_path, self.icon, self.id)
                )
            conn.commit()

    def delete(self):
        import sqlite3
        from config import Config
        if self.id:
            with sqlite3.connect(Config.SOUNDBOARDS_DB) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM sounds WHERE id = ?", (self.id,))
                conn.commit()

    @staticmethod
    def get_by_id(sound_id):
        import sqlite3
        from config import Config
        with sqlite3.connect(Config.SOUNDBOARDS_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM sounds WHERE id = ?", (sound_id,))
            row = cur.fetchone()
            if row:
                return Sound(id=row['id'], soundboard_id=row['soundboard_id'], name=row['name'], 
                             file_path=row['file_path'], icon=row['icon'])
        return None

    def __repr__(self):
        return f'<Sound {self.name}>'
