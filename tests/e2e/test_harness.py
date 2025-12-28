import re
from playwright.sync_api import Page, expect

def test_harness_smoke(page: Page, live_server_url):
    """Verify the server starts and the browser can load the homepage."""
    page.goto(live_server_url)
    expect(page).to_have_title(re.compile(r".*Home.*"))
    expect(page.get_by_text("Welcome to Soundboard")).to_be_visible()
