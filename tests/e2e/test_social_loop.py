import re
import time

from playwright.sync_api import Browser, expect

from tests.e2e.playwright_helper import PlaywrightHelper


def test_social_interactions(browser: Browser, live_server_url, test_db_setup):
    """Test Follow, Rate, and Notifications between two users."""
    accounts_db, _ = test_db_setup

    # 1. Setup User A (Board Owner)
    context_a = browser.new_context()
    page_a = context_a.new_page()
    helper_a = PlaywrightHelper(page_a, live_server_url, accounts_db)
    user_a = f"owner_{int(time.time())}"
    helper_a.register_and_login(user_a, f"{user_a}@test.com", "Pass123!")

    # User A creates a public board
    board_name = "Public Board"
    page_a.goto(f"{live_server_url}/soundboard/create")
    page_a.get_by_label("Soundboard Name").fill(board_name)
    page_a.get_by_label("Public (Shared with everyone)").check()
    page_a.get_by_role("button", name="Save").click()

    # Get board ID from URL
    expect(page_a).to_have_url(f"{live_server_url}/soundboard/dashboard")
    view_link = page_a.get_by_role("link", name="View").first
    board_url = view_link.get_attribute("href")
    assert board_url is not None
    board_id = board_url.split("/")[-1]

    # 2. Setup User B (Follower/Rater)
    context_b = browser.new_context()
    page_b = context_b.new_page()
    helper_b = PlaywrightHelper(page_b, live_server_url, accounts_db)
    user_b = f"follower_{int(time.time())}"
    helper_b.register_and_login(user_b, f"{user_b}@test.com", "Pass123!")

    # User B follows User A
    page_b.goto(
        f"{live_server_url}/auth/user/{user_a}"
    )  # The route is auth.public_profile -> /user/<username>
    page_b.get_by_role("button", name="Follow").click()
    expect(page_b.get_by_role("button", name="Unfollow")).to_be_visible()

    # User B rates User A's board
    page_b.goto(f"{live_server_url}/soundboard/view/{board_id}")
    # Click the 4th star (index 3)
    stars = page_b.locator(".rating-star")
    stars.nth(3).click()

    # Verify rating toast or update
    # Toast might be fast, but average rating should update
    expect(page_b.locator("#avg-rating")).to_have_text(re.compile(r"4(\.0)?"))

    # 3. Verify Notification for User A
    page_a.goto(f"{live_server_url}/index")

    # Trigger poll manually to avoid 15s wait
    page_a.evaluate("refreshNotifications()")

    # Open notification dropdown
    page_a.locator("#notifDropdown").click()
    expect(page_a.get_by_text(f"{user_b} rated your soundboard")).to_be_visible()

    context_a.close()
    context_b.close()
