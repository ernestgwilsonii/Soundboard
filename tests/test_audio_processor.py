from unittest.mock import MagicMock, patch

import pytest

from app.utils.audio import AudioProcessor


def test_get_metadata_success():
    """Test extracting metadata from a valid file."""
    mock_mutagen = MagicMock()
    mock_mutagen.info.length = 120.5
    mock_mutagen.info.sample_rate = 44100

    with patch("app.utils.audio.mutagen.File", return_value=mock_mutagen):
        with patch("app.utils.audio.os.path.getsize", return_value=5000):
            metadata = AudioProcessor.get_metadata("dummy/path/song.mp3")

            assert metadata["duration"] == 120.5
            assert metadata["sample_rate"] == 44100


def test_get_metadata_invalid_file():
    """Test handling of invalid files."""
    with patch("app.utils.audio.mutagen.File", return_value=None):
        metadata = AudioProcessor.get_metadata("dummy/path/invalid.txt")
        assert metadata is None


def test_get_metadata_advanced_success():
    """Test extracting advanced metadata (bitrate, size, format)."""
    mock_mutagen = MagicMock()
    mock_mutagen.info.length = 60.0
    mock_mutagen.info.sample_rate = 44100
    mock_mutagen.info.bitrate = 128000
    # Type check or mock for format
    mock_mutagen.__class__.__name__ = "MP3"

    with patch("app.utils.audio.mutagen.File", return_value=mock_mutagen):
        with patch("app.utils.audio.os.path.getsize", return_value=1024 * 1024):  # 1MB
            metadata = AudioProcessor.get_metadata("dummy/path/song.mp3")

            assert metadata["bitrate"] == 128
            assert metadata["file_size"] == 1048576
            assert metadata["format"] == "MP3"

    """Test that the normalize method exists and runs without error (stub)."""
    # Should not raise exception
    try:
        AudioProcessor.normalize("dummy/path.mp3")
    except Exception as e:
        pytest.fail(f"normalize raised exception: {e}")
