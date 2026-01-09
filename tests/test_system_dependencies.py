import shutil


def test_ffmpeg_installed():
    """Verify that ffmpeg is available in the system PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    assert (
        ffmpeg_path is not None
    ), "ffmpeg must be installed on the system for audio normalization"
