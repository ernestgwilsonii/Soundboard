import pytest
from playwright.sync_api import Page, expect, Browser
from tests.e2e.playwright_helper import PlaywrightHelper
import time

def test_instant_invite_notification(browser: Browser, live_server_url, test_db_setup):
    """
    Verifies that an invite triggers a notification instantly on the recipient's screen.
    This is the core of our Live Collaboration infrastructure.
    """
    accounts_db, _ = test_db_setup
    
    # 1. SETUP ALICE (Owner)
    ctx_a = browser.new_context()
    page_a = ctx_a.new_page()
    helper_a = PlaywrightHelper(page_a, live_server_url, accounts_db)
    helper_a.register_and_login("Alice", "alice@test.com", "pass123")
    
    # Alice creates a board
    page_a.goto(f"{live_server_url}/soundboard/create")
    page_a.get_by_label("Soundboard Name").fill("Live Project")
    page_a.get_by_role("button", name="Save").click()
    
    # Get Board ID
    page_a.goto(f"{live_server_url}/soundboard/dashboard")
    card = page_a.locator(".card", has_text="Live Project")
    edit_link = card.get_by_role("link", name="Edit")
    board_url = edit_link.get_attribute("href")
    board_id = board_url.split('/')[-1]
    
    # 2. SETUP BOB (Collaborator)
    ctx_b = browser.new_context()
    page_b = ctx_b.new_page()
    helper_b = PlaywrightHelper(page_b, live_server_url, accounts_db)
    helper_b.register_and_login("Bob", "bob@test.com", "pass123")
    
    # Bob is just sitting on the home page, waiting...
    page_b.goto(f"{live_server_url}/")
    # Verify no badge initially
    expect(page_b.locator("#notifDropdown .badge")).not_to_be_visible()
    
    # 3. ALICE INVITES BOB
    page_a.goto(f"{live_server_url}/soundboard/edit/{board_id}")
    page_a.get_by_placeholder("Username").fill("Bob")
    # This action triggers the instant broadcast
    page_a.get_by_role("button", name="Add Editor").click()
    
    # 4. BOB RECEIVES NOTIFICATION INSTANTLY
    # Check for the SweetAlert2 toast heading
    expect(page_b.get_by_role("heading", name="Alice invited you to collaborate")).to_be_visible(timeout=10000)
    # Check for the red badge update
    expect(page_b.locator("#notifDropdown .badge")).to_be_visible()
    
    ctx_a.close()
    ctx_b.close()