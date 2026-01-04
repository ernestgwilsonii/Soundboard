import os
import signal
import subprocess
import time

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module", autouse=True)
def server():
    print("\nStarting server...")
    # Run server and capture output
    proc = subprocess.Popen(
        ["venv/bin/python", "soundboard.py"],
        env={**os.environ, "FLASK_RUN_PORT": "5001", "FLASK_DEBUG": "0"},
    )

    time.sleep(5)  # Wait for startup
    if proc.poll() is not None:
        raise Exception(f"Server died immediately with code {proc.returncode}")

    yield "http://127.0.0.1:5001"
    print("Stopping server...")
    os.kill(proc.pid, signal.SIGTERM)


def test_homepage_loads(page: Page, server):
    page.goto(server)
    expect(page).to_have_title(compiled_regex=r".*Home.*")
    print("SUCCESS: Homepage verified.")
