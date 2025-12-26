import pytest
from unittest.mock import patch, MagicMock
from app.utils.audio import AudioProcessor

def test_get_metadata_success():
    """Test extracting metadata from a valid file."""
    mock_mutagen = MagicMock()
    mock_mutagen.info.length = 120.5
    mock_mutagen.info.sample_rate = 44100
    
    with patch('app.utils.audio.mutagen.File', return_value=mock_mutagen):
        metadata = AudioProcessor.get_metadata('dummy/path/song.mp3')
        
        assert metadata['duration'] == 120.5
        assert metadata['sample_rate'] == 44100

def test_get_metadata_invalid_file():
    """Test handling of invalid files."""
    with patch('app.utils.audio.mutagen.File', return_value=None):
        metadata = AudioProcessor.get_metadata('dummy/path/invalid.txt')
        assert metadata is None

def test_get_metadata_error():
    """Test handling of mutagen errors."""
    with patch('app.utils.audio.mutagen.File', side_effect=Exception("Read error")):
        metadata = AudioProcessor.get_metadata('dummy/path/corrupt.mp3')
        assert metadata is None

def test_normalize_hook_stub():
    """Test that the normalize method exists and runs without error (stub)."""
    # Should not raise exception
    try:
        AudioProcessor.normalize('dummy/path.mp3')
    except Exception as e:
        pytest.fail(f"normalize raised exception: {e}")
