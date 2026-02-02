import os
import subprocess

import pytest


def test_mypy_config_exists():
    """Check if pyproject.toml exists and contains mypy config, or mypy.ini exists."""
    has_pyproject = False
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r") as f:
            if "[tool.mypy]" in f.read():
                has_pyproject = True

    has_mypy_ini = os.path.exists("mypy.ini")

    assert (
        has_pyproject or has_mypy_ini
    ), "No mypy configuration found in pyproject.toml or mypy.ini"


def test_mypy_installed():
    """Check if mypy is installed."""
    try:
        subprocess.run(["mypy", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("mypy is not installed")
