from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_accounts_db, get_soundboards_db

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
        db = get_accounts_db()
        cur = db.cursor()
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
        db.commit()

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            return User(id=row['id'], username=row['username'], email=row['email'], 
                        password_hash=row['password_hash'], role=row['role'])
        return None

    @staticmethod
    def get_by_id(user_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return User(id=row['id'], username=row['username'], email=row['email'], 
                        password_hash=row['password_hash'], role=row['role'])
        return None

    def __repr__(self):
        return f'<User {self.username}>'

class Soundboard:
    def __init__(self, id=None, name=None, user_id=None, icon=None, is_public=False):
        self.id = id
        self.name = name
        self.user_id = user_id
        self.icon = icon
        self.is_public = bool(is_public)

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO soundboards (name, user_id, icon, is_public) VALUES (?, ?, ?, ?)",
                (self.name, self.user_id, self.icon, int(self.is_public))
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE soundboards SET name=?, user_id=?, icon=?, is_public=? WHERE id=?",
                (self.name, self.user_id, self.icon, int(self.is_public), self.id)
            )
        db.commit()

    def delete(self):
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            # Also delete associated sounds
            cur.execute("DELETE FROM sounds WHERE soundboard_id = ?", (self.id,))
            cur.execute("DELETE FROM soundboards WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(soundboard_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE id = ?", (soundboard_id,))
        row = cur.fetchone()
        if row:
            return Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                             icon=row['icon'], is_public=row['is_public'])
        return None

    @staticmethod
    def get_by_user_id(user_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE user_id = ? ORDER BY name ASC", (user_id,))
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public']) for row in rows]

    @staticmethod
    def get_public():
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE is_public = 1 ORDER BY name ASC")
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public']) for row in rows]

    @staticmethod
    def get_recent_public(limit=6):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE is_public = 1 ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public']) for row in rows]

    @staticmethod
    def search(query):
        from app.db import get_accounts_db, get_soundboards_db
        from config import Config
        
        # We need to search across two databases. 
        # This is tricky with raw SQLite. 
        # Strategy: 
        # 1. Find user IDs matching query in accounts DB.
        # 2. Search soundboards DB for matching names OR matching user IDs.
        # 3. Search soundboards DB for matching sounds and get their soundboard IDs.
        
        user_ids = []
        accounts_db = get_accounts_db()
        ac_cur = accounts_db.cursor()
        ac_cur.execute("SELECT id FROM users WHERE username LIKE ?", (f'%{query}%',))
        user_ids = [row['id'] for row in ac_cur.fetchall()]
        
        soundboards_db = get_soundboards_db()
        sb_cur = soundboards_db.cursor()
        
        # Build query for soundboards
        search_query = "SELECT DISTINCT id, name, user_id, icon, is_public FROM soundboards WHERE is_public = 1 AND (name LIKE ?"
        params = [f'%{query}%']
        
        if user_ids:
            placeholders = ','.join(['?'] * len(user_ids))
            search_query += f" OR user_id IN ({placeholders})"
            params.extend(user_ids)
            
        # Search sounds and get their board IDs
        sb_cur.execute("SELECT DISTINCT soundboard_id FROM sounds WHERE name LIKE ?", (f'%{query}%',))
        sound_sb_ids = [row['soundboard_id'] for row in sb_cur.fetchall()]
        
        if sound_sb_ids:
            placeholders = ','.join(['?'] * len(sound_sb_ids))
            search_query += f" OR id IN ({placeholders})"
            params.extend(sound_sb_ids)
            
        search_query += ") ORDER BY name ASC"
        
        sb_cur.execute(search_query, params)
        rows = sb_cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public']) for row in rows]

    def get_sounds(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM sounds WHERE soundboard_id = ? ORDER BY name ASC", (self.id,))
        rows = cur.fetchall()
        return [Sound(id=row['id'], soundboard_id=row['soundboard_id'], name=row['name'], 
                      file_path=row['file_path'], icon=row['icon']) for row in rows]

    def get_creator_username(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
        row = cur.fetchone()
        return row['username'] if row else 'Unknown'

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
        db = get_soundboards_db()
        cur = db.cursor()
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
        db.commit()

    def delete(self):
        if self.id:
            import os
            from flask import current_app
            db = get_soundboards_db()
            cur = db.cursor()
            
            # Remove the actual file
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # Also remove custom icon if it's a file
            if self.icon and '/' in self.icon:
                icon_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.icon)
                if os.path.exists(icon_full_path):
                    # We should be careful about shared icons, but for now we delete it
                    os.remove(icon_full_path)

            cur.execute("DELETE FROM sounds WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(sound_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM sounds WHERE id = ?", (sound_id,))
        row = cur.fetchone()
        if row:
            return Sound(id=row['id'], soundboard_id=row['soundboard_id'], name=row['name'], 
                         file_path=row['file_path'], icon=row['icon'])
        return None

    def __repr__(self):
        return f'<Sound {self.name}>'
