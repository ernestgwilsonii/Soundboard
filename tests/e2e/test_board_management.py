from playwright.sync_api import Page, expect
from tests.e2e.playwright_helper import PlaywrightHelper
import time
import re

def test_soundboard_lifecycle(page: Page, live_server_url, test_db_setup):
    """Test Create, Edit, and Delete a soundboard."""
    accounts_db, _ = test_db_setup
    helper = PlaywrightHelper(page, live_server_url, accounts_db)
    
    username = f"board_user_{int(time.time())}"
    email = f"{username}@test.com"
    password = "SecretPassword123!"
    
    # Login
    helper.register_and_login(username, email, password)
    
    # 1. Create
    board_name = f"My Cool Board {int(time.time())}"
    helper.create_soundboard(board_name)
    
    # After creation, it should redirect to dashboard and show the board
    expect(page).to_have_url(f"{live_server_url}/soundboard/dashboard")
    expect(page.get_by_role("heading", name=board_name)).to_be_visible()
    
    # 2. Edit
    # Click Edit button for our board
    page.get_by_role("link", name="Edit").first.click()
    
    expect(page).to_have_url(re.compile(rf"{live_server_url}/soundboard/edit/\d+"))
    
    new_name = board_name + " Updated"
    page.get_by_label("Soundboard Name").fill(new_name)
    page.get_by_role("button", name="Save").click()
    
    # Should redirect to view page
    expect(page).to_have_url(re.compile(rf"{live_server_url}/soundboard/view/\d+"))
    expect(page.get_by_role("heading", level=1)).to_have_text(new_name)
    
    # 3. Delete
    # Go back to Edit to delete (View page should have an Edit link for owner)
    page.get_by_role("link", name="Edit").click()
    
    # Click Delete Soundboard
    page.get_by_role("button", name="Delete Soundboard").click()
    
    # Handle SweetAlert2 confirm
    page.get_by_role("button", name="Delete Everything").click()
    
    # Should redirect to dashboard and show "Soundboard deleted." flash
    expect(page).to_have_url(f"{live_server_url}/soundboard/dashboard")
    expect(page.get_by_text("Soundboard deleted.")).to_be_visible()
    expect(page.get_by_text(new_name)).not_to_be_visible()