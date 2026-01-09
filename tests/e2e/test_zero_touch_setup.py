from playwright.sync_api import Page, expect


def test_first_user_auto_admin(page: Page, live_server_url, test_db_setup):
    """
    Automated verification of the 'Zero-Touch Admin' feature.
    1. Start with fresh DB (handled by test_db_setup).
    2. Register the very first user.
    3. Assert the user is automatically an admin and verified.
    """

    # 1. Registration
    username = "SystemAdmin"
    email = "admin@example.com"
    password = "AdminPassword123!"

    page.goto(f"{live_server_url}/auth/register")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_label("Repeat Password").fill(password)
    page.get_by_role("button", name="Register").click()

    # 2. Verify Flash Message
    expect(
        page.get_by_text("Congratulations, you are now a registered user!")
    ).to_be_visible()
    expect(page.get_by_text("promoted to Administrator")).to_be_visible()

    # 3. Login
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign In").click()

    # 4. Verify Admin Menu is visible
    # The Admin menu has id='adminDropdown' in base.html
    admin_menu = page.locator("#adminDropdown")
    expect(admin_menu).to_be_visible()
    expect(admin_menu).to_contain_text("Admin")

    # 5. Verify email verification status (Expert feature)
    # Check profile page to see if verification warning is NOT there
    page.goto(f"{live_server_url}/auth/profile")
    # If the user was NOT verified, we'd typically see a warning or 'Unverified' badge.
    # In our app, verification_required decorator flashes a message.
    # But for the profile page, we can just check if we can access admin routes.
    page.goto(f"{live_server_url}/admin/settings")
    expect(page).to_have_url(f"{live_server_url}/admin/settings")
    expect(page.get_by_role("heading", name="Admin Settings")).to_be_visible()


def test_second_user_is_regular_user(page: Page, live_server_url, test_db_setup):
    """
    Verify that only the FIRST user gets admin.
    """
    # 1. Register first user (Admin)
    page.goto(f"{live_server_url}/auth/register")
    page.get_by_label("Username").fill("Admin1")
    page.get_by_label("Email").fill("admin1@example.com")
    page.get_by_label("Password", exact=True).fill("pass")
    page.get_by_label("Repeat Password").fill("pass")
    page.get_by_role("button", name="Register").click()

    # 2. Register second user (Regular)
    page.goto(f"{live_server_url}/auth/register")
    page.get_by_label("Username").fill("RegularUser")
    page.get_by_label("Email").fill("regular@example.com")
    page.get_by_label("Password", exact=True).fill("pass")
    page.get_by_label("Repeat Password").fill("pass")
    page.get_by_role("button", name="Register").click()

    # Check flash message - should NOT mention promotion
    expect(page.get_by_text("promoted to Administrator")).not_to_be_visible()

    # Login as second user
    page.get_by_label("Username or Email").fill("RegularUser")
    page.get_by_label("Password").fill("pass")
    page.get_by_role("button", name="Sign In").click()

    # Verify Admin menu is MISSING
    expect(page.locator("#adminDropdown")).not_to_be_visible()

    # Try to access admin settings directly
    page.goto(f"{live_server_url}/admin/settings")
    # Should redirect to index with permission error
    expect(page.get_by_text("You do not have permission")).to_be_visible()
