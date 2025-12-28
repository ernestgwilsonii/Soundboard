import pytest
from unittest.mock import patch, MagicMock
from app.utils.audio import AudioProcessor

def test_normalize_success():
    """Test that normalization correctly calls pydub methods."""
    mock_audio = MagicMock()
    mock_audio.dBFS = -30.0 # Quiet audio
    
    mock_normalized = MagicMock()
    mock_audio.apply_gain.return_value = mock_normalized
    
    # Mocking AudioSegment.from_file
    with patch('app.utils.audio.AudioSegment.from_file', return_value=mock_audio) as mock_from_file:
        result = AudioProcessor.normalize('dummy/path/song.mp3')
        
        assert result is True
        mock_from_file.assert_called_once_with('dummy/path/song.mp3')
        mock_audio.apply_gain.assert_called_once()
        # Check that export was called on the NORMALIZED object
        mock_normalized.export.assert_called_once_with('dummy/path/song.mp3', format='mp3')

def test_normalize_error_loading():
    """Test handling of errors when loading the file."""
    with patch('app.utils.audio.AudioSegment.from_file', side_effect=Exception("Load error")):
        result = AudioProcessor.normalize('dummy/path/bad.mp3')
        assert result is False

def test_normalize_error_exporting():
    """Test handling of errors when exporting the file."""
    mock_audio = MagicMock()
    mock_audio.dBFS = -10.0
    
    mock_normalized = MagicMock()
    mock_normalized.export.side_effect = Exception("Export error")
    mock_audio.apply_gain.return_value = mock_normalized
    
    with patch('app.utils.audio.AudioSegment.from_file', return_value=mock_audio):
        result = AudioProcessor.normalize('dummy/path/bad_export.mp3')
        assert result is False

@pytest.mark.parametrize("extension, expected_format", [
    ("mp3", "mp3"),
    ("wav", "wav"),
    ("ogg", "ogg"),
    ("OGG", "ogg")
])
def test_normalize_different_formats(extension, expected_format):
    """Test that normalization correctly identifies and uses the file format from extension."""
    mock_audio = MagicMock()
    mock_audio.dBFS = -15.0
    mock_normalized = MagicMock()
    mock_audio.apply_gain.return_value = mock_normalized
    
    file_path = f'test_audio.{extension}'
    
    with patch('app.utils.audio.AudioSegment.from_file', return_value=mock_audio):
        result = AudioProcessor.normalize(file_path)
        assert result is True
        mock_normalized.export.assert_called_once_with(file_path, format=expected_format)
