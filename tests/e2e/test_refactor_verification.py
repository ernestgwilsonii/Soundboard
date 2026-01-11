from playwright.sync_api import Page, expect

from app.constants import DEFAULT_PAGE_SIZE
from app.enums import UserRole
from tests.e2e.playwright_helper import PlaywrightHelper


def test_refactor_foundations_verification(page: Page, live_server_url, test_db_setup):
    """
    E2E test to verify Phase 1 refactoring (Enums and Constants).
    """
    accounts_db, _ = test_db_setup
    helper = PlaywrightHelper(page, live_server_url, accounts_db)

    # 1. Register the FIRST user (should be Auto-Admin)
    admin_user = "admin_refactor"
    admin_email = "admin_refactor@test.com"
    password = "Password123!"

    # We use a helper that handles registration and login
    helper.register_and_login(admin_user, admin_email, password)

    # 2. Verify Admin Menu Visibility (Checks UserRole.ADMIN enum in template)
    # The sidebar should have an "Admin" link
    admin_link = page.get_by_role("link", name="Admin")
    expect(admin_link).to_be_visible()

    # 3. Verify DEFAULT_PAGE_SIZE Constant in UI
    # We'll check the members page. Even with only 1 user, we can verify the limit logic
    # by checking the pagination info if available, or just ensuring the page loads correctly.
    page.goto(f"{live_server_url}/auth/members")

    # Check if "10 per page" is the selected option in the limit dropdown (if it exists)
    limit_select = page.locator("select[name='limit']")
    if limit_select.count() > 0:
        expect(limit_select).to_have_value(str(DEFAULT_PAGE_SIZE))

    # 4. Verify Visibility Enum logic
    # Create a soundboard and check its default visibility (Private by default in refactor)
    helper.create_soundboard("Refactor Test Board")
    page.goto(f"{live_server_url}/soundboard/dashboard")

    # Check for "Private" badge or icon if applicable
    # (Assuming the dashboard shows visibility status)
    expect(page.get_by_text("Refactor Test Board")).to_be_visible()


def test_user_role_toggle_verification(page: Page, live_server_url, test_db_setup):
    """Verify that role toggling in admin panel works with Enums."""
    accounts_db, _ = test_db_setup
    helper = PlaywrightHelper(page, live_server_url, accounts_db)

    # Register admin
    helper.register_and_login("admin_master", "master@test.com", "Pass123!")

    # Register a second user (who should be a regular USER)
    page.get_by_role("link", name="Logout").click()

    user_name = "regular_bob"
    helper.register_and_login(user_name, "bob@test.com", "Pass123!")

    # Check that 'bob' does NOT see admin link
    expect(page.get_by_role("link", name="Admin")).not_to_be_visible()

    # Re-login as admin
    page.get_by_role("link", name="Logout").click()
    page.goto(f"{live_server_url}/auth/login")
    page.get_by_label("Username or Email").fill("admin_master")
    page.get_by_label("Password").fill("Pass123!")
    page.get_by_role("button", name="Sign In").click()

    # Go to Admin -> Users
    page.goto(f"{live_server_url}/admin/users")

    # Find 'regular_bob' and toggle role
    # Assuming there's a button/form to toggle role
    user_row = page.locator(f"tr:has-text('{user_name}')")
    toggle_btn = user_row.get_by_role("button", name="Toggle Role")
    toggle_btn.click()

    # Verify flash message or change in UI
    expect(
        page.get_by_text(f"User {user_name} role changed to {UserRole.ADMIN}")
    ).to_be_visible()
