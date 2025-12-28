import sqlite3
from playwright.sync_api import Page, expect

class PlaywrightHelper:
    def __init__(self, page: Page, base_url: str, accounts_db_path: str):
        self.page = page
        self.base_url = base_url
        self.db_path = accounts_db_path

    def register_and_login(self, username, email, password):
        """Creates a fresh user, marks them verified in DB, and logs in."""
        # 1. Register
        self.page.goto(f"{self.base_url}/auth/register")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Email").fill(email)
        self.page.get_by_label("Password", exact=True).fill(password)
        self.page.get_by_label("Confirm Password").fill(password)
        self.page.get_by_role("button", name="Register").click()
        
        # 2. Bypass Email Verification via DB
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE users SET is_verified = 1 WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        
        # 3. Login
        self.page.goto(f"{self.base_url}/auth/login")
        # The label is "Username or Email" now
        self.page.get_by_label("Username or Email").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign In").click()
        
        # Verify success
        expect(self.page).to_have_url(f"{self.base_url}/")
        return username

    def create_soundboard(self, name):
        """Quickly creates a soundboard."""
        self.page.goto(f"{self.base_url}/soundboard/create")
        self.page.get_by_label("Soundboard Name").fill(name)
        self.page.get_by_role("button", name="Save").click()
        return name
