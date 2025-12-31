import pytest
import os
import io
from unittest.mock import patch
from app import create_app
from app.models import User, Soundboard, Sound
from config import Config
import sqlite3

@pytest.fixture
def client(monkeypatch):
    # Use temporary DBs
    accounts_db = os.path.abspath('test_accounts_audio.sqlite3')
    soundboards_db = os.path.abspath('test_soundboards_audio.sqlite3')
    
    monkeypatch.setattr(Config, 'ACCOUNTS_DB', accounts_db)
    monkeypatch.setattr(Config, 'SOUNDBOARDS_DB', soundboards_db)
    
    # Mock UPLOAD_FOLDER to a temp dir
    import tempfile
    upload_folder = tempfile.mkdtemp()
    monkeypatch.setattr(Config, 'UPLOAD_FOLDER', upload_folder)
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize DBs
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)
        
    with app.app_context():
        with sqlite3.connect(accounts_db) as conn:
            with open('app/schema_accounts.sql', 'r') as f:
                conn.executescript(f.read())
        with sqlite3.connect(soundboards_db) as conn:
            with open('app/schema_soundboards.sql', 'r') as f:
                conn.executescript(f.read())
                
    with app.test_client() as client:
        yield client
        
    # Cleanup
    import shutil
    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)
    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path): os.remove(db_path)

def test_upload_sound_metadata_extraction(client):
    """Test that uploading a sound triggers metadata extraction and saves duration."""
    from app.models import User, Soundboard, Sound
    
    # Setup User and Soundboard
    with client.application.app_context():
        u = User(username='audiouser', email='audio@test.com', is_verified=True)
        u.set_password('password')
        u.save()
        sb = Soundboard(name='Audio Board', user_id=u.id)
        sb.save()
        sb_id = sb.id

    client.post('/auth/login', data={'username': 'audiouser', 'password': 'password'})
    
    # Mock AudioProcessor
    with patch('app.soundboard.routes.AudioProcessor') as MockProcessor:
        # Configure mock to return specific metadata
        MockProcessor.get_metadata.return_value = {
            'duration': 123.45, 
            'sample_rate': 44100,
            'bitrate': 128,
            'file_size': 5000,
            'format': 'MP3'
        }
        MockProcessor.normalize.return_value = True
        
        # Create dummy audio file
        data = {
            'name': 'Test Sound',
            'audio_file': (io.BytesIO(b"dummy audio data"), 'test.mp3')
        }
        
        response = client.post(f'/soundboard/{sb_id}/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        
        # Verify Sound record FIRST to see if logic executed
        with client.application.app_context():
            s = Sound.get_by_id(1)
            assert s is not None, "Sound was not saved to DB"
            assert s.name == 'Test Sound'
            assert s.end_time == 123.45, f"Expected end_time 123.45, got {s.end_time}"
            assert s.bitrate == 128
            assert s.file_size == 5000
            assert s.format == 'MP3'
            
        assert response.status_code == 200
        if b'uploaded!' not in response.data:
             print(f"FLASH MESSAGE MISSING. Response contains: {response.data.decode('utf-8')}")
        assert b'uploaded!' in response.data
        
        # Verify Sound record
        with client.application.app_context():
            # Get the sound we just uploaded (should be the only one)
            s = Sound.get_by_id(1)
            assert s is not None
            assert s.name == 'Test Sound'
            # THIS IS THE KEY ASSERTION: duration should be saved in end_time
            assert s.end_time == 123.45
            
        # Verify normalize was called
        MockProcessor.normalize.assert_called_once()
