import os
import re
import time

from playwright.sync_api import Page, expect

from tests.e2e.playwright_helper import PlaywrightHelper


def test_waveform_editor_interaction(page: Page, live_server_url, test_db_setup):
    """Test that the Waveform Editor loads and handles updates inputs."""
    accounts_db, _ = test_db_setup
    helper = PlaywrightHelper(page, live_server_url, accounts_db)

    # 1. Setup User and Board
    username = f"wf_user_{int(time.time())}"

    # Login
    helper.register_and_login(username, f"{username}@test.com", "Pass123!")

    # Force dashboard if not already there
    if "/soundboard/dashboard" not in page.url:
        page.goto(f"{live_server_url}/soundboard/dashboard")

    board_name = "Editor Test Board"
    helper.create_soundboard(board_name)

    # Verify we are on dashboard and board is visible
    expect(page).to_have_url(f"{live_server_url}/soundboard/dashboard")
    expect(page.get_by_role("heading", name=board_name)).to_be_visible()

    # 2. Go to Edit Page
    # Use more specific selector to avoid navbar links
    page.locator(".card-body").get_by_role("link", name="Edit").first.click()
    expect(page).to_have_url(re.compile(rf"{live_server_url}/soundboard/edit/\d+"))

    # 3. Upload a sound
    test_audio_path = os.path.abspath("sounds/1/test.mp3")
    if not os.path.exists(test_audio_path):
        # Create a dummy if missing (though it should exist per my check)
        pass

    page.get_by_role("link", name="Upload Sound").click()
    page.get_by_label("Sound Name").fill("Trim Me")
    page.set_input_files("input[name='audio_file']", test_audio_path)
    page.get_by_role("button", name="Upload").click()

    # Should redirect back to edit page
    expect(page).to_have_url(re.compile(rf"{live_server_url}/soundboard/edit/\d+"))
    expect(page.get_by_text("Trim Me", exact=True)).to_be_visible()

    # 4. Open Trimming Modal
    page.get_by_role("button", name="Settings").click()

    # Wait for waveform and region to be ready in JS
    page.wait_for_function(
        "window.waveformEditor && window.waveformEditor.activeRegion", timeout=15000
    )

    start_input = page.locator("#modal-start")
    end_input = page.locator("#modal-end")

    # Verify inputs populated
    expect(start_input).to_have_value("0.000")
    expect(end_input).not_to_have_value("")

    # 5. Simulate dragging by updating region via JS
    page.evaluate(
        """
        const region = window.waveformEditor.activeRegion;
        region.setOptions({ start: 0.2, end: 0.8 });
        // Manually trigger the update to sync inputs
        window.waveformEditor.wsRegions.emit('region-updated', region);
    """
    )

    # Check if inputs updated
    page.wait_for_function("document.getElementById('modal-start').value === '0.200'")
    expect(start_input).to_have_value("0.200")
    expect(end_input).to_have_value("0.800")

    # 6. Save and check persistence
    page.get_by_role("button", name="Save changes").click()

    # Wait for reload
    page.wait_for_load_state("networkidle")

    # Open again
    page.get_by_role("button", name="Settings").click()
    # Should not be 0 anymore
    expect(start_input).not_to_have_value("0.000")
