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
