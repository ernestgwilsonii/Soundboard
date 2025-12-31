from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from app.db import get_accounts_db, get_soundboards_db

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password_hash=None, role='user', 
                 active=True, is_verified=False, avatar_path=None, 
                 failed_login_attempts=0, lockout_until=None,
                 bio=None, social_x=None, social_youtube=None, social_website=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.active = bool(active)
        self.is_verified = bool(is_verified)
        self.avatar_path = avatar_path
        self.failed_login_attempts = int(failed_login_attempts)
        self.lockout_until = lockout_until
        self.bio = bio
        self.social_x = social_x
        self.social_youtube = social_youtube
        self.social_website = social_website

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
                "INSERT INTO users (username, email, password_hash, role, active, is_verified, avatar_path, failed_login_attempts, lockout_until, bio, social_x, social_youtube, social_website) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.username, self.email, self.password_hash, self.role, int(self.active), int(self.is_verified), self.avatar_path, self.failed_login_attempts, self.lockout_until, self.bio, self.social_x, self.social_youtube, self.social_website)
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE users SET username=?, email=?, password_hash=?, role=?, active=?, is_verified=?, avatar_path=?, failed_login_attempts=?, lockout_until=?, bio=?, social_x=?, social_youtube=?, social_website=? WHERE id=?",
                (self.username, self.email, self.password_hash, self.role, int(self.active), int(self.is_verified), self.avatar_path, self.failed_login_attempts, self.lockout_until, self.bio, self.social_x, self.social_youtube, self.social_website, self.id)
            )
        db.commit()

    def delete(self):
        """
        Permanently deletes the user and all associated data (boards, sounds, playlists, etc.).
        """
        if not self.id:
            return
            
        db_ac = get_accounts_db()
        db_sb = get_soundboards_db()
        
        # 1. Delete Soundboards (this handles sounds and files via Soundboard.delete)
        sbs = Soundboard.get_by_user_id(self.id)
        for sb in sbs:
            sb.delete()
            
        # 2. Delete Playlists
        pls = Playlist.get_by_user_id(self.id)
        for pl in pls:
            pl.delete()
            
        # 3. Cleanup social records
        db_sb.execute("DELETE FROM ratings WHERE user_id = ?", (self.id,))
        db_sb.execute("DELETE FROM comments WHERE user_id = ?", (self.id,))
        db_sb.execute("DELETE FROM activities WHERE user_id = ?", (self.id,))
        db_sb.commit()
        
        # 4. Cleanup account records
        db_ac.execute("DELETE FROM favorites WHERE user_id = ?", (self.id,))
        db_ac.execute("DELETE FROM notifications WHERE user_id = ?", (self.id,))
        db_ac.execute("DELETE FROM users WHERE id = ?", (self.id,))
        db_ac.commit()
        
        # 5. Delete avatar file if exists
        if self.avatar_path:
            import os
            from flask import current_app
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.avatar_path)
            if os.path.exists(full_path):
                os.remove(full_path)

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
                        is_verified=row['is_verified'], avatar_path=row['avatar_path'],
                        failed_login_attempts=row['failed_login_attempts'], lockout_until=row['lockout_until'],
                        bio=row['bio'], social_x=row['social_x'], social_youtube=row['social_youtube'], social_website=row['social_website'])
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
                        is_verified=row['is_verified'], avatar_path=row['avatar_path'],
                        failed_login_attempts=row['failed_login_attempts'], lockout_until=row['lockout_until'],
                        bio=row['bio'], social_x=row['social_x'], social_youtube=row['social_youtube'], social_website=row['social_website'])
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
                        is_verified=row['is_verified'], avatar_path=row['avatar_path'],
                        failed_login_attempts=row['failed_login_attempts'], lockout_until=row['lockout_until'],
                        bio=row['bio'], social_x=row['social_x'], social_youtube=row['social_youtube'], social_website=row['social_website'])
        return None

    @staticmethod
    def get_all(limit=10, offset=0, sort_by='newest', search_query=None):
        db = get_accounts_db()
        cur = db.cursor()
        
        sql = "SELECT * FROM users WHERE 1=1"
        params = []
        
        if search_query:
            sql += " AND username LIKE ?"
            params.append(f'%{search_query}%')
            
        if sort_by == 'popular':
            # This is complex because follows table is in accounts DB now (correct)
            # We can join with a subquery of follow counts
            sql = f"""
                SELECT u.*, COUNT(f.follower_id) as follower_count 
                FROM ({sql}) u
                LEFT JOIN follows f ON u.id = f.followed_id
                GROUP BY u.id
                ORDER BY follower_count DESC, u.username ASC
            """
        elif sort_by == 'oldest':
            sql += " ORDER BY created_at ASC"
        elif sort_by == 'alpha':
            sql += " ORDER BY username ASC"
        else: # newest
            sql += " ORDER BY created_at DESC"
            
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [User(id=row['id'], username=row['username'], email=row['email'], 
                     password_hash=row['password_hash'], role=row['role'], active=row['active'],
                     is_verified=row['is_verified'], avatar_path=row['avatar_path'],
                     failed_login_attempts=row['failed_login_attempts'], lockout_until=row['lockout_until'],
                     bio=row['bio'], social_x=row['social_x'], social_youtube=row['social_youtube'], social_website=row['social_website']) for row in rows]

    @staticmethod
    def count_all(search_query=None):
        db = get_accounts_db()
        cur = db.cursor()
        sql = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []
        if search_query:
            sql += " AND username LIKE ?"
            params.append(f'%{search_query}%')
        cur.execute(sql, params)
        return cur.fetchone()[0]

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

    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import datetime, timedelta
            self.lockout_until = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
        self.save()

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.lockout_until = None
        self.save()

    def is_locked(self):
        if not self.lockout_until:
            return False
        from datetime import datetime
        lockout_time = datetime.strptime(self.lockout_until, '%Y-%m-%d %H:%M:%S')
        if datetime.now() > lockout_time:
            # Lock expired
            return False
        return True

    def follow(self, user_id):
        if self.id == user_id:
            return
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (self.id, user_id)
        )
        db.commit()

    def unfollow(self, user_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
            (self.id, user_id)
        )
        db.commit()

    def is_following(self, user_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
            (self.id, user_id)
        )
        return cur.fetchone() is not None

    def get_followers(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("""
            SELECT u.* FROM users u
            JOIN follows f ON u.id = f.follower_id
            WHERE f.followed_id = ?
            ORDER BY u.username ASC
        """, (self.id,))
        rows = cur.fetchall()
        return [User(id=row['id'], username=row['username'], email=row['email'], 
                     password_hash=row['password_hash'], role=row['role'], active=row['active'],
                     is_verified=row['is_verified'], avatar_path=row['avatar_path'],
                     failed_login_attempts=row['failed_login_attempts'], lockout_until=row['lockout_until'],
                     bio=row['bio'], social_x=row['social_x'], social_youtube=row['social_youtube'], social_website=row['social_website']) for row in rows]

    def get_following(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("""
            SELECT u.* FROM users u
            JOIN follows f ON u.id = f.followed_id
            WHERE f.follower_id = ?
            ORDER BY u.username ASC
        """, (self.id,))
        rows = cur.fetchall()
        return [User(id=row['id'], username=row['username'], email=row['email'], 
                     password_hash=row['password_hash'], role=row['role'], active=row['active'],
                     is_verified=row['is_verified'], avatar_path=row['avatar_path'],
                     failed_login_attempts=row['failed_login_attempts'], lockout_until=row['lockout_until'],
                     bio=row['bio'], social_x=row['social_x'], social_youtube=row['social_youtube'], social_website=row['social_website']) for row in rows]

    def get_follower_count(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM follows WHERE followed_id = ?", (self.id,))
        return cur.fetchone()[0]

    def get_following_count(self):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ?", (self.id,))
        return cur.fetchone()[0]

class Soundboard:
    def __init__(self, id=None, name=None, user_id=None, icon=None, is_public=False, theme_color='#0d6efd', theme_preset='default'):
        self.id = id
        self.name = name
        self.user_id = user_id
        self.icon = icon
        self.is_public = bool(is_public)
        self.theme_color = theme_color
        self.theme_preset = theme_preset

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO soundboards (name, user_id, icon, is_public, theme_color, theme_preset) VALUES (?, ?, ?, ?, ?, ?)",
                (self.name, self.user_id, self.icon, int(self.is_public), self.theme_color, self.theme_preset)
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE soundboards SET name=?, user_id=?, icon=?, is_public=?, theme_color=?, theme_preset=? WHERE id=?",
                (self.name, self.user_id, self.icon, int(self.is_public), self.theme_color, self.theme_preset, self.id)
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
                             icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                             theme_preset=row['theme_preset'])
        return None

    @staticmethod
    def get_all():
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards ORDER BY name ASC")
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                          theme_preset=row['theme_preset']) for row in rows]

    @staticmethod
    def get_by_user_id(user_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE user_id = ? ORDER BY name ASC", (user_id,))
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                          theme_preset=row['theme_preset']) for row in rows]

    @staticmethod
    def get_public(order_by='recent'):
        db = get_soundboards_db()
        cur = db.cursor()
        
        if order_by == 'trending':
            return Soundboard.get_trending()

        sql = "SELECT * FROM soundboards WHERE is_public = 1"
        if order_by == 'top':
            # Order by average rating
            sql = """
                SELECT s.*, AVG(r.score) as avg_score 
                FROM soundboards s 
                LEFT JOIN ratings r ON s.id = r.soundboard_id 
                WHERE s.is_public = 1 
                GROUP BY s.id 
                ORDER BY avg_score DESC, s.name ASC
            """
        elif order_by == 'name':
            sql += " ORDER BY name ASC"
        else: # recent
            sql += " ORDER BY created_at DESC, id DESC"
            
        cur.execute(sql)
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                          theme_preset=row['theme_preset']) for row in rows]

    @staticmethod
    def get_by_tag(tag_name):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("""
            SELECT s.* FROM soundboards s
            JOIN soundboard_tags st ON s.id = st.soundboard_id
            JOIN tags t ON st.tag_id = t.id
            WHERE t.name = ? AND s.is_public = 1
            ORDER BY s.name ASC
        """, (tag_name.lower().strip(),))
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                          theme_preset=row['theme_preset']) for row in rows]

    @staticmethod
    def get_recent_public(limit=6):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM soundboards WHERE is_public = 1 ORDER BY created_at DESC, id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                          theme_preset=row['theme_preset']) for row in rows]

    @staticmethod
    def get_trending(limit=10):
        """
        Calculates trending soundboards based on a weighted score:
        Score = (AvgRating * Count) + (CreatorFollowers * 2)
        Includes a time decay (only looks at public boards).
        """
        db_sb = get_soundboards_db()
        db_ac = get_accounts_db()
        
        # We perform a joined score calculation
        # 1. Get rating stats
        cur_sb = db_sb.cursor()
        cur_sb.execute("""
            SELECT s.id, AVG(r.score) as avg_score, COUNT(r.id) as rating_count
            FROM soundboards s
            LEFT JOIN ratings r ON s.id = r.soundboard_id
            WHERE s.is_public = 1
            GROUP BY s.id
        """)
        sb_stats = {row['id']: (row['avg_score'] or 0, row['rating_count']) for row in cur_sb.fetchall()}
        
        # 2. Get all public boards to build full list
        all_public = Soundboard.get_public(order_by='recent')
        
        # 3. Calculate scores
        scored_boards = []
        for sb in all_public:
            avg, count = sb_stats.get(sb.id, (0, 0))
            
            # Fetch creator followers from accounts DB
            cur_ac = db_ac.cursor()
            cur_ac.execute("SELECT COUNT(*) FROM follows WHERE followed_id = ?", (sb.user_id,))
            followers = cur_ac.fetchone()[0]
            
            # Weighted Score Formula
            score = (avg * count) + (followers * 2)
            scored_boards.append((sb, score))
            
        # Sort by score descending
        scored_boards.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored_boards[:limit]]

    @staticmethod
    def get_featured():
        featured_id = AdminSettings.get_setting('featured_soundboard_id')
        if featured_id:
            sb = Soundboard.get_by_id(featured_id)
            if sb and sb.is_public:
                return sb
        
        # Fallback to most trending public board
        trending = Soundboard.get_trending(limit=1)
        return trending[0] if trending else None

    @staticmethod
    def search(query, order_by='recent'):
        from app.db import get_accounts_db, get_soundboards_db
        from config import Config
        
        user_ids = []
        accounts_db = get_accounts_db()
        ac_cur = accounts_db.cursor()
        ac_cur.execute("SELECT id FROM users WHERE username LIKE ?", (f'%{query}%',))
        user_ids = [row['id'] for row in ac_cur.fetchall()]
        
        soundboards_db = get_soundboards_db()
        sb_cur = soundboards_db.cursor()
        
        # Build query for soundboards
        search_query = "SELECT DISTINCT id, name, user_id, icon, is_public, theme_color, theme_preset FROM soundboards WHERE is_public = 1 AND (name LIKE ?"
        params = [f'%{query}%']
        
        if user_ids:
            placeholders = ','.join(['?'] * len(user_ids))
            search_query += f" OR user_id IN ({placeholders})"
            params.extend(user_ids)
            
        sb_cur.execute("SELECT DISTINCT soundboard_id FROM sounds WHERE name LIKE ?", (f'%{query}%',))
        sound_sb_ids = [row['soundboard_id'] for row in sb_cur.fetchall()]
        
        if sound_sb_ids:
            placeholders = ','.join(['?'] * len(sound_sb_ids))
            search_query += f" OR id IN ({placeholders})"
            params.extend(sound_sb_ids)
            
        # Search tags and get their board IDs
        sb_cur.execute("""
            SELECT DISTINCT soundboard_id FROM soundboard_tags st
            JOIN tags t ON st.tag_id = t.id
            WHERE t.name LIKE ?
        """, (f'%{query}%',))
        tag_sb_ids = [row['soundboard_id'] for row in sb_cur.fetchall()]
        
        if tag_sb_ids:
            placeholders = ','.join(['?'] * len(tag_sb_ids))
            search_query += f" OR id IN ({placeholders})"
            params.extend(tag_sb_ids)
            
        search_query += ")"
        
        if order_by == 'top':
            # Join with ratings for search
            final_query = f"""
                SELECT results.*, AVG(r.score) as avg_score 
                FROM ({search_query}) as results 
                LEFT JOIN ratings r ON results.id = r.soundboard_id 
                GROUP BY results.id 
                ORDER BY avg_score DESC, results.name ASC
            """
            sb_cur.execute(final_query, params)
        elif order_by == 'name':
            search_query += " ORDER BY name ASC"
            sb_cur.execute(search_query, params)
        else: # recent
            search_query += " ORDER BY created_at DESC, id DESC"
            sb_cur.execute(search_query, params)
            
        rows = sb_cur.fetchall()
        return [Soundboard(id=row['id'], name=row['name'], user_id=row['user_id'], 
                          icon=row['icon'], is_public=row['is_public'], theme_color=row['theme_color'],
                          theme_preset=row['theme_preset']) for row in rows]

    def get_sounds(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM sounds WHERE soundboard_id = ? ORDER BY display_order ASC, name ASC", (self.id,))
        rows = cur.fetchall()
        return [Sound(id=row['id'], soundboard_id=row['soundboard_id'], name=row['name'], 
                      file_path=row['file_path'], icon=row['icon'], display_order=row['display_order'],
                      volume=row['volume'], is_loop=row['is_loop'], 
                      start_time=row['start_time'], end_time=row['end_time'],
                      hotkey=row['hotkey'], bitrate=row['bitrate'],
                      file_size=row['file_size'], format=row['format']) for row in rows]

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

    def get_user_rating(self, user_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT score FROM ratings WHERE soundboard_id = ? AND user_id = ?", (self.id, user_id))
        row = cur.fetchone()
        return row['score'] if row else 0

    def get_comments(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM comments WHERE soundboard_id = ? ORDER BY created_at DESC", (self.id,))
        rows = cur.fetchall()
        return [Comment(id=row['id'], user_id=row['user_id'], soundboard_id=row['soundboard_id'], 
                        text=row['text'], created_at=row['created_at']) for row in rows]

    def get_tags(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("""
            SELECT t.* FROM tags t 
            JOIN soundboard_tags st ON t.id = st.tag_id 
            WHERE st.soundboard_id = ? 
            ORDER BY t.name ASC
        """, (self.id,))
        rows = cur.fetchall()
        return [Tag(id=row['id'], name=row['name']) for row in rows]

    def add_tag(self, tag_name):
        db = get_soundboards_db()
        tag = Tag.get_or_create(tag_name)
        if not tag: return
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO soundboard_tags (soundboard_id, tag_id) VALUES (?, ?)",
            (self.id, tag.id)
        )
        db.commit()

    def remove_tag(self, tag_name):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("""
            DELETE FROM soundboard_tags 
            WHERE soundboard_id = ? AND tag_id IN (SELECT id FROM tags WHERE name = ?)
        """, (self.id, tag_name.lower().strip()))
        db.commit()

    def __repr__(self):
        return f'<Soundboard {self.name}>'

class Sound:
    def __init__(self, id=None, soundboard_id=None, name=None, file_path=None, icon=None, 
                 display_order=0, volume=1.0, is_loop=False, start_time=0.0, end_time=None, hotkey=None,
                 bitrate=None, file_size=None, format=None):
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
        self.hotkey = hotkey
        self.bitrate = bitrate
        self.file_size = file_size
        self.format = format

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            if self.display_order == 0:
                cur.execute("SELECT MAX(display_order) FROM sounds WHERE soundboard_id = ?", (self.soundboard_id,))
                max_row = cur.fetchone()
                max_order = max_row[0] if max_row and max_row[0] is not None else 0
                self.display_order = (max_order + 1)

            cur.execute(
                "INSERT INTO sounds (soundboard_id, name, file_path, icon, display_order, volume, is_loop, start_time, end_time, hotkey, bitrate, file_size, format) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.soundboard_id, self.name, self.file_path, self.icon, self.display_order, self.volume, int(self.is_loop), self.start_time, self.end_time, self.hotkey, self.bitrate, self.file_size, self.format)
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE sounds SET soundboard_id=?, name=?, file_path=?, icon=?, display_order=?, volume=?, is_loop=?, start_time=?, end_time=?, hotkey=?, bitrate=?, file_size=?, format=? WHERE id=?",
                (self.soundboard_id, self.name, self.file_path, self.icon, self.display_order, self.volume, int(self.is_loop), self.start_time, self.end_time, self.hotkey, self.bitrate, self.file_size, self.format, self.id)
            )
        db.commit()

    def delete(self):
        if self.id:
            import os
            from flask import current_app
            db = get_soundboards_db()
            cur = db.cursor()
            
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            
            if self.icon and '/' in self.icon:
                icon_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.icon)
                if os.path.exists(icon_full_path):
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
                         start_time=row['start_time'], end_time=row['end_time'],
                         hotkey=row['hotkey'], bitrate=row['bitrate'], 
                         file_size=row['file_size'], format=row['format'])
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

    def get_author(self):
        return User.get_by_id(self.user_id)

class Playlist:
    def __init__(self, id=None, user_id=None, name=None, description=None, is_public=False, created_at=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.is_public = bool(is_public)
        self.created_at = created_at

    def save(self):
        db = get_soundboards_db()
        cur = db.cursor()
        if self.id is None:
            cur.execute(
                "INSERT INTO playlists (user_id, name, description, is_public) VALUES (?, ?, ?, ?)",
                (self.user_id, self.name, self.description, int(self.is_public))
            )
            self.id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE playlists SET name=?, description=?, is_public=? WHERE id=?",
                (self.name, self.description, int(self.is_public), self.id)
            )
        db.commit()

    def delete(self):
        if self.id:
            db = get_soundboards_db()
            cur = db.cursor()
            cur.execute("DELETE FROM playlist_items WHERE playlist_id = ?", (self.id,))
            cur.execute("DELETE FROM playlists WHERE id = ?", (self.id,))
            db.commit()

    @staticmethod
    def get_by_id(playlist_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
        row = cur.fetchone()
        if row:
            return Playlist(id=row['id'], user_id=row['user_id'], name=row['name'], 
                            description=row['description'], is_public=row['is_public'], 
                            created_at=row['created_at'])
        return None

    @staticmethod
    def get_by_user_id(user_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM playlists WHERE user_id = ? ORDER BY name ASC", (user_id,))
        rows = cur.fetchall()
        return [Playlist(id=row['id'], user_id=row['user_id'], name=row['name'], 
                         description=row['description'], is_public=row['is_public'], 
                         created_at=row['created_at']) for row in rows]

    def get_sounds(self):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("""
            SELECT s.* FROM sounds s 
            JOIN playlist_items pi ON s.id = pi.sound_id 
            WHERE pi.playlist_id = ? 
            ORDER BY pi.display_order ASC
        """, (self.id,))
        rows = cur.fetchall()
        return [Sound(id=row['id'], soundboard_id=row['soundboard_id'], name=row['name'], 
                      file_path=row['file_path'], icon=row['icon'], display_order=row['display_order'],
                      volume=row['volume'], is_loop=row['is_loop'], 
                      start_time=row['start_time'], end_time=row['end_time'],
                      bitrate=row['bitrate'], file_size=row['file_size'], 
                      format=row['format']) for row in rows]

    def add_sound(self, sound_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT MAX(display_order) FROM playlist_items WHERE playlist_id = ?", (self.id,))
        max_row = cur.fetchone()
        order = (max_row[0] + 1) if max_row and max_row[0] is not None else 1
        
        cur.execute(
            "INSERT INTO playlist_items (playlist_id, sound_id, display_order) VALUES (?, ?, ?)",
            (self.id, sound_id, order)
        )
        db.commit()

    def remove_sound(self, sound_id):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("DELETE FROM playlist_items WHERE playlist_id = ? AND sound_id = ?", (self.id, sound_id))
        db.commit()

class PlaylistItem:
    def __init__(self, id=None, playlist_id=None, sound_id=None, display_order=0):
        self.id = id
        self.playlist_id = playlist_id
        self.sound_id = sound_id
        self.display_order = display_order

class Tag:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    @staticmethod
    def get_or_create(name):
        name = name.lower().strip()
        if not name: return None
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM tags WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return Tag(id=row['id'], name=row['name'])
        
        cur.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        db.commit()
        return Tag(id=cur.lastrowid, name=name)

    @staticmethod
    def get_all():
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM tags ORDER BY name ASC")
        rows = cur.fetchall()
        return [Tag(id=row['id'], name=row['name']) for row in rows]

    @staticmethod
    def get_popular(limit=10):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("""
            SELECT t.*, COUNT(st.soundboard_id) as count 
            FROM tags t 
            JOIN soundboard_tags st ON t.id = st.tag_id 
            GROUP BY t.id 
            ORDER BY count DESC 
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        return [Tag(id=row['id'], name=row['name']) for row in rows]

class Activity:
    def __init__(self, id=None, user_id=None, action_type=None, description=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.action_type = action_type
        self.description = description
        self.created_at = created_at

    @staticmethod
    def record(user_id, action_type, description):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO activities (user_id, action_type, description) VALUES (?, ?, ?)",
            (user_id, action_type, description)
        )
        db.commit()

    @staticmethod
    def get_recent(limit=20):
        db = get_soundboards_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM activities ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [Activity(id=row['id'], user_id=row['user_id'], action_type=row['action_type'],
                         description=row['description'], created_at=row['created_at']) for row in rows]

    def get_user(self):
        return User.get_by_id(self.user_id)

class Notification:
    def __init__(self, id=None, user_id=None, type=None, message=None, link=None, is_read=False, created_at=None):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.message = message
        self.link = link
        self.is_read = bool(is_read)
        self.created_at = created_at

    @staticmethod
    def add(user_id, type, message, link=None):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO notifications (user_id, type, message, link) VALUES (?, ?, ?, ?)",
            (user_id, type, message, link)
        )
        db.commit()

    @staticmethod
    def get_unread_for_user(user_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC", (user_id,))
        rows = cur.fetchall()
        return [Notification(id=row['id'], user_id=row['user_id'], type=row['type'],
                            message=row['message'], link=row['link'], is_read=row['is_read'],
                            created_at=row['created_at']) for row in rows]

    @staticmethod
    def mark_all_read(user_id):
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        db.commit()

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