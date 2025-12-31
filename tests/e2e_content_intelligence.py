import pytest
from playwright.sync_api import Page, expect
import time
import subprocess
import os
import signal
import socket

@pytest.fixture(scope="module")
def server():
    # Find an open port
    def get_open_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    port = get_open_port()
    addr = f"http://127.0.0.1:{port}"
    
    print(f"[E2E] Starting server on {addr}...")
    proc = subprocess.Popen(["venv/bin/python", "soundboard.py"], 
                            env={**os.environ, "FLASK_RUN_PORT": str(port), "FLASK_DEBUG": "0"})
    
    # Wait for server
    start = time.time()
    while time.time() - start < 10:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                print("[E2E] Server is UP!")
                break
        except:
            time.sleep(0.5)
    else:
        proc.kill()
        raise Exception("Server failed to start for E2E tests")
        
    yield addr
    print("[E2E] Stopping server...")
    os.kill(proc.pid, signal.SIGTERM)

def test_signup_validation_ui(page: Page, server):
    """Test the real-time availability check on signup."""
    page.goto(f"{server}/auth/register")
    
    # Type 'dingus' which we know is taken
    username_input = page.locator('input[name="username"]')
    username_input.fill('dingus')
    
    # Wait for AJAX check
    page.wait_for_timeout(500)
    
    # Should show as invalid (red)
    expect(username_input).to_have_class(r".*is-invalid.*")
    
    # Type a random new user
    new_user = f"user_{int(time.time())}"
    username_input.fill(new_user)
    
    # Wait for AJAX check
    page.wait_for_timeout(500)
    
    # Should show as valid (green)
    expect(username_input).to_have_class(r".*is-valid.*")
    print(f"SUCCESS: Real-time validation verified for '{new_user}'")

def test_gallery_trending_sort(page: Page, server):
    """Test that the Trending sort option exists in the Gallery."""
    page.goto(f"{server}/soundboard/gallery")
    
    # Open sort dropdown
    page.click('#sortDropdown')
    
    # Verify 'Trending' option exists
    expect(page.locator('text=Trending')).to_be_visible()
    print("SUCCESS: Trending sort option verified in Gallery.")

def test_password_strength_meter(page: Page, server):
    """Test that the password meter reacts to input."""
    page.goto(f"{server}/auth/register")
    
    pass_input = page.locator('input[name="password"]')
    pass_input.fill('weak')
    expect(page.locator('#password-strength-text')).to_have_text('Strength: Weak')
    
    pass_input.fill('VeryStrongPassword123!')
    expect(page.locator('#password-strength-text')).to_have_text('Strength: Strong')
    print("SUCCESS: Password strength meter verified.")

