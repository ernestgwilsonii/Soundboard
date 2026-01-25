import pytest

"""Tests for application constants."""


def test_constants_file_exists():
    """Verify that app/constants.py exists and can be imported."""
    try:
        import app.constants

        assert app.constants is not None
    except ImportError:
        pytest.fail("app/constants.py does not exist or cannot be imported")


def test_pagination_constants():
    """Verify default pagination constants."""
    from app.constants import DEFAULT_PAGE_SIZE, MAX_ITEMS_PER_PAGE

    assert DEFAULT_PAGE_SIZE == 10
    assert MAX_ITEMS_PER_PAGE == 50


def test_audio_constants():
    """Verify audio processing constants."""
    from app.constants import NORMALIZATION_TARGET_DBFS

    assert NORMALIZATION_TARGET_DBFS == -20.0
