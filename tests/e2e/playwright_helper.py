import sqlite3
import os
from playwright.sync_api import Page, expect

class PlaywrightHelper:
    def __init__(self, page: Page, base_url: str, accounts_db_path: str):
        self.page = page
        self.base_url = base_url
        self.db_path = accounts_db_path

    def register_and_login(self, username, email, password):
        """Creates a fresh user, marks them verified via route, and logs in."""
        # 1. Register
        self.page.goto(f"{self.base_url}/auth/register")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Email").fill(email)
        self.page.get_by_label("Password", exact=True).fill(password)
        self.page.get_by_label("Repeat Password").fill(password)
        self.page.get_by_role("button", name="Register").click()
        
        # 2. Verify via App Route (Most reliable for session)
        # We need to generate a valid token for this user
        from itsdangerous import URLSafeTimedSerializer
        # We need the secret key from the actual app config or environment
        secret = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
        s = URLSafeTimedSerializer(secret)
        token = s.dumps(email, salt='email-verify')
        
        self.page.goto(f"{self.base_url}/auth/verify/{token}")
        
        # Support both regular verification and Auto-Admin (already verified) cases
        try:
            expect(self.page.get_by_text("Your account has been verified!")).to_be_visible(timeout=2000)
        except:
            # If they were the first user, they might see 'already verified' or just be on login
            pass
        
        # 3. Login
        self.page.goto(f"{self.base_url}/auth/login")
        self.page.get_by_label("Username or Email").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign In").click()
        
        # Verify success - support both / and /index
        import re
        expect(self.page).to_have_url(re.compile(f"{self.base_url}/(index)?$"))
        
        # Force navigation to dashboard
        self.page.goto(f"{self.base_url}/soundboard/dashboard")
        return username

    def create_soundboard(self, name):
        """Quickly creates a soundboard."""
        self.page.goto(f"{self.base_url}/soundboard/create")
        self.page.get_by_label("Soundboard Name").fill(name)
        self.page.get_by_role("button", name="Save").click()
        # Force navigation to dashboard
        self.page.goto(f"{self.base_url}/soundboard/dashboard")
        return name
