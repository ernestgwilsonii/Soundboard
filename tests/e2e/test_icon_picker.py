import re
import time

from playwright.sync_api import Page, expect

from tests.e2e.playwright_helper import PlaywrightHelper


def test_icon_picker_dynamic_loading(page: Page, live_server_url, test_db_setup):
    """Test that the Icon Picker loads FA6 icons and updates the form."""
    accounts_db, _ = test_db_setup
    helper = PlaywrightHelper(page, live_server_url, accounts_db)

    # 1. Setup User and Go to Create Soundboard
    username = f"icon_user_{int(time.time())}"
    helper.register_and_login(username, f"{username}@test.com", "Pass123!")

    page.goto(f"{live_server_url}/soundboard/create")

    # 2. Click the Icon Input to trigger picker
    icon_input = page.locator("#icon-input")
    icon_input.click()

    # 3. Verify Modal and Loading
    modal = page.locator("#iconPickerModal")
    expect(modal).to_be_visible()

    # Grid should eventually have icons (wait for network load from GitHub)
    # The spinner should disappear
    icon_grid = modal.locator("#iconGrid")
    # Wait for at least one icon option to appear
    first_icon = icon_grid.locator(".icon-option").first
    expect(first_icon).to_be_visible(timeout=20000)

    # 4. Search for an icon
    search_input = modal.locator("#iconSearchInput")
    search_input.fill("dog")

    # Wait for filtered results
    dog_icon = icon_grid.locator(".icon-option[title='Dog']").first
    expect(dog_icon).to_be_visible(timeout=5000)

    # 5. Select the icon
    icon_class = dog_icon.get_attribute("data-class")
    assert icon_class is not None
    dog_icon.click()

    # Modal should close
    expect(modal).not_to_be_visible()

    # Input and preview should update
    expect(icon_input).to_have_value(icon_class)
    expect(page.locator("#icon-preview")).to_have_class(
        re.compile(rf".*{icon_class}.*")
    )

    # 6. Complete creation and verify persistence
    board_name = "Icon Test Board"
    page.get_by_label("Soundboard Name").fill(board_name)
    page.get_by_role("button", name="Save").click()

    # Should be on dashboard, verify icon class in HTML
    expect(page).to_have_url(f"{live_server_url}/soundboard/dashboard")
    expect(page.locator(f"i.{icon_class.replace(' ', '.')}").first).to_be_visible()
