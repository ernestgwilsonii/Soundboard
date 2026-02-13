import os
import subprocess

import pytest


def test_pre_commit_config_exists():
    """Check if .pre-commit-config.yaml exists."""
    assert os.path.exists(".pre-commit-config.yaml")


def test_quality_script_exists():
    """Check if scripts/check_quality.sh exists."""
    assert os.path.exists("scripts/check_quality.sh")


def test_quality_script_executable():
    """Check if scripts/check_quality.sh is executable."""
    assert os.access("scripts/check_quality.sh", os.X_OK)


def test_pre_commit_installed():
    """Check if pre-commit is installed."""
    try:
        subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try looking in venv/bin
        venv_pre = os.path.join("venv", "bin", "pre-commit")
        if os.path.exists(venv_pre):
            subprocess.run([venv_pre, "--version"], check=True, capture_output=True)
        else:
            pytest.fail("pre-commit is not installed")
