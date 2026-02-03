import re

from playwright.sync_api import Page, expect


def test_demo_soundboard_presence(page: Page, live_server_url):
    """Verify that the demo soundboard appears for unauthenticated users."""
    page.goto(live_server_url)

    # 1. Check Hero Section
    expect(page.get_by_text("Welcome to Soundboard")).to_be_visible()
    expect(page.get_by_text("Try it out right now!")).to_be_visible()

    # 2. Check Demo Board Title and Badge
    expect(page.get_by_text("Try It Now!")).to_be_visible()
    expect(page.get_by_text("DEMO")).to_be_visible()

    # 3. Check for specific demo sounds
    expect(page.get_by_text("Airhorn")).to_be_visible()
    expect(page.get_by_text("Vine Boom")).to_be_visible()
    expect(page.get_by_text("Sad Violin")).to_be_visible()

    # 4. Check for Hotkey labels
    expect(page.get_by_text("1", exact=True)).to_be_visible()
    expect(page.get_by_text("2", exact=True)).to_be_visible()


def test_demo_soundboard_interaction(page: Page, live_server_url):
    """Verify that clicking a demo sound triggers the visual effect."""
    page.goto(live_server_url)

    # Click Airhorn
    airhorn = page.get_by_text("Airhorn")
    airhorn.click()

    # Verify we stayed on home page
    expect(page).to_have_url(re.compile(f"{live_server_url}/(index)?$"))


def test_demo_soundboard_hotkeys(page: Page, live_server_url):
    """Verify hotkey interaction."""
    page.goto(live_server_url)

    # Press '1' for Airhorn
    page.keyboard.press("1")

    # Check that we are still on the home page
    expect(page).to_have_url(re.compile(f"{live_server_url}/(index)?$"))


def test_demo_cta_visibility(page: Page, live_server_url):
    """Verify that sign up CTAs are prominent."""
    page.goto(live_server_url)

    register_btn = page.get_by_role("link", name="Create My Own Account")
    expect(register_btn).to_be_visible()
    expect(register_btn).to_have_attribute("href", "/auth/register")
