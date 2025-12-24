from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from app.db import get_accounts_db, get_soundboards_db

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password_hash=None, role='user', active=True, is_verified=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.active = bool(active)
        self.is_verified = bool(is_verified)

    @property
    def is_active(self):
        return self.active

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def save(self):
        db = get_accounts_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, role, active, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
                (self.username, self.email, self.password_hash, self.role, int(self.active), int(self.is_verified))
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE users SET username=?, email=?, password_hash=?, role=?, active=?, is_verified=? WHERE id=?",
                (self.username, self.email, self.password_hash, self.role, int(self.active), int(self.is_verified), self.id)
            )
        db.commit()

    def add_favorite(self, soundboard_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO favorites (user_id, soundboard_id) VALUES (?, ?)",
            (self.id, soundboard_id)
        )
        db.commit()

    def remove_favorite(self, soundboard_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "DELETE FROM favorites WHERE user_id = ? AND soundboard_id = ?",
            (self.id, soundboard_id)
        )
        db.commit()

    def get_favorites(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT soundboard_id FROM favorites WHERE user_id = ?", (self.id,))
        rows = cur.fetchall()
        return [row['soundboard_id'] for row in rows]

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
                        password_hash=row['password_hash'], role=row['role'], active=row['active'],
                        is_verified=row['is_verified'])
        return None

    @staticmethod
    def get_by_email(email):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            return User(id=row['id'], username=row['username'], email=row['email'], 
                        password_hash=row['password_hash'], role=row['role'], active=row['active'],
                        is_verified=row['is_verified'])
        return None

    @staticmethod
    def get_by_id(user_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return User(id=row['id'], username=row['username'], email=row['email'], 
                        password_hash=row['password_hash'], role=row['role'], active=row['active'],
                        is_verified=row['is_verified'])
        return None

    @staticmethod
    def get_all():
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users ORDER BY username ASC")
        rows = cur.fetchall()
        return [User(id=row['id'], username=row['username'], email=row['email'], 
                     password_hash=row['password_hash'], role=row['role'], active=row['active'],
                     is_verified=row['is_verified']) for row in rows]

    def __repr__(self):
        return f'<User {self.username}>'

    def get_token(self, salt):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt=salt)

    @staticmethod
    def verify_token(token, salt, expiration=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt=salt, max_age=expiration)
        except:
            return None
        return User.get_by_email(email)

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
    def get_all():
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards ORDER BY name ASC")
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public']) for row in rows]

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
        cur.execute("SELECT * FROM soundboards WHERE is_public = 1 ORDER BY created_at DESC, id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public']) for row in rows]

    @staticmethod
    def get_featured():
        featured_id = AdminSettings.get_setting('featured_soundboard_id')
        if featured_id:
            sb = Soundboard.get_by_id(featured_id)
            if sb and sb.is_public:
                return sb
        
        # Fallback to most recent public board
        recent = Soundboard.get_recent_public(limit=1)
        return recent[0] if recent else None

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
        cur.execute("SELECT * FROM sounds WHERE soundboard_id = ? ORDER BY display_order ASC, name ASC", (self.id,))
        rows = cur.fetchall()
        return [Sound(id=row['id'], soundboard_id=row['soundboard_id'], name=row['name'], 
                      file_path=row['file_path'], icon=row['icon'], display_order=row['display_order'],
                      volume=row['volume'], is_loop=row['is_loop'], 
                      start_time=row['start_time'], end_time=row['end_time']) for row in rows]

    def get_creator_username(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
        row = cur.fetchone()
        return row['username'] if row else 'Unknown'

    def get_average_rating(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT AVG(score) as avg, COUNT(*) as count FROM ratings WHERE soundboard_id = ?", (self.id,))
        row = cur.fetchone()
        return {
            'average': round(row['avg'], 1) if row['avg'] else 0,
            'count': row['count']
        }

    def get_comments(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM comments WHERE soundboard_id = ? ORDER BY created_at DESC", (self.id,))
        rows = cur.fetchall()
        return [Comment(id=row['id'], user_id=row['user_id'], soundboard_id=row['soundboard_id'], 
                        text=row['text'], created_at=row['created_at']) for row in rows]

    def __repr__(self):
        return f'<Soundboard {self.name}>'

class Sound:
    def __init__(self, id=None, soundboard_id=None, name=None, file_path=None, icon=None, 
                 display_order=0, volume=1.0, is_loop=False, start_time=0.0, end_time=None):
        self.id = id
        self.soundboard_id = soundboard_id
        self.name = name
        self.file_path = file_path
        self.icon = icon
        self.display_order = display_order
        self.volume = volume
        self.is_loop = bool(is_loop)
        self.start_time = start_time
        self.end_time = end_time

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            # If display_order is 0 (default), find the next available order
            if self.display_order == 0:
                cur.execute("SELECT MAX(display_order) FROM sounds WHERE soundboard_id = ?", (self.soundboard_id,))
                max_row = cur.fetchone()
                max_order = max_row[0] if max_row and max_row[0] is not None else 0
                self.display_order = (max_order + 1)

            cur.execute(
                "INSERT INTO sounds (soundboard_id, name, file_path, icon, display_order, volume, is_loop, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.soundboard_id, self.name, self.file_path, self.icon, self.display_order, self.volume, int(self.is_loop), self.start_time, self.end_time)
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE sounds SET soundboard_id=?, name=?, file_path=?, icon=?, display_order=?, volume=?, is_loop=?, start_time=?, end_time=? WHERE id=?",
                (self.soundboard_id, self.name, self.file_path, self.icon, self.display_order, self.volume, int(self.is_loop), self.start_time, self.end_time, self.id)
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
                         file_path=row['file_path'], icon=row['icon'], display_order=row['display_order'],
                         volume=row['volume'], is_loop=row['is_loop'], 
                         start_time=row['start_time'], end_time=row['end_time'])
        return None

    def __repr__(self):
        return f'<Sound {self.name}>'

class Rating:
    def __init__(self, id=None, user_id=None, soundboard_id=None, score=0, created_at=None):
        self.id = id
        self.user_id = user_id
        self.soundboard_id = soundboard_id
        self.score = score
        self.created_at = created_at

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO ratings (user_id, soundboard_id, score) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, soundboard_id) DO UPDATE SET score=excluded.score",
                (self.user_id, self.soundboard_id, self.score)
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE ratings SET score=? WHERE id=?",
                (self.score, self.id)
            )
        db.commit()

class Comment:
    def __init__(self, id=None, user_id=None, soundboard_id=None, text=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.soundboard_id = soundboard_id
        self.text = text
        self.created_at = created_at

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO comments (user_id, soundboard_id, text) VALUES (?, ?, ?)",
                (self.user_id, self.soundboard_id, self.text)
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE comments SET text=? WHERE id=?",
                (self.text, self.id)
            )
        db.commit()

    def delete(self):
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            cur.execute("DELETE FROM comments WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(comment_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        row = cur.fetchone()
        if row:
            return Comment(id=row['id'], user_id=row['user_id'], soundboard_id=row['soundboard_id'], 
                           text=row['text'], created_at=row['created_at'])
        return None

    def get_author_username(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
        row = cur.fetchone()
        return row['username'] if row else 'Unknown'

class AdminSettings:
    @staticmethod
    def get_setting(key, default=None):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return row['value']
        return default

    @staticmethod
    def set_setting(key, value):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO admin_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
        db.commit()
