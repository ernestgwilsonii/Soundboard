import time

from playwright.sync_api import Page, expect

from tests.e2e.playwright_helper import PlaywrightHelper


def test_full_auth_flow(page: Page, live_server_url, test_db_setup):
    """Test Signup, DB Verification, and Login with both Username and Email."""
    accounts_db, _ = test_db_setup
    helper = PlaywrightHelper(page, live_server_url, accounts_db)

    username = f"user_{int(time.time())}"
    email = f"{username}@test.com"
    password = "SecretPassword123!"

    # 1. Signup & Login (Helper handles DB verification bypass)
    helper.register_and_login(username, email, password)

    # Verify we are on home and see logout
    expect(page.get_by_role("link", name="Logout")).to_be_visible()

    # 2. Logout
    page.get_by_role("link", name="Logout").click()
    import re

    expect(page).to_have_url(re.compile(f"{live_server_url}/(index)?$"))
    expect(page.get_by_role("link", name="Login")).to_be_visible()

    # 3. Login with Email
    page.get_by_role("link", name="Login").click()
    page.get_by_label("Username or Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url(re.compile(f"{live_server_url}/(index)?$"))
    expect(page.get_by_role("link", name="Logout")).to_be_visible()
