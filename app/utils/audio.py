from pydub import AudioSegment
import mutagen
import os
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    @staticmethod
    def get_metadata(file_path):
        """
        Extracts metadata (duration, sample_rate) from an audio file.
        Returns a dictionary or None if extraction fails.
        """
        try:
            audio = mutagen.File(file_path)
            if audio is None or not audio.info:
                logger.warning(f"Could not read metadata from {file_path}")
                return None
            
            return {
                'duration': round(audio.info.length, 3),
                'sample_rate': getattr(audio.info, 'sample_rate', 0),
                'bitrate': getattr(audio.info, 'bitrate', 0) // 1000 if hasattr(audio.info, 'bitrate') else 0,
                'file_size': os.path.getsize(file_path),
                'format': type(audio).__name__
            }
        except Exception as e:
            logger.error(f"Error processing audio metadata for {file_path}: {e}")
            return None

    @staticmethod
    def normalize(file_path, target_dbfs=-20.0):
        """
        Normalizes the audio volume to a target dBFS level.
        Overwrites the original file.
        """
        try:
            audio = AudioSegment.from_file(file_path)
            change_in_dbfs = target_dbfs - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dbfs)
            
            # Determine format from extension
            ext = os.path.splitext(file_path)[1][1:].lower()
            if ext == 'sbp': # Should not happen here but safety first
                ext = 'zip'
            
            normalized_audio.export(file_path, format=ext)
            logger.info(f"Normalized {file_path} to {target_dbfs} dBFS")
            return True
        except Exception as e:
            logger.error(f"Error normalizing audio for {file_path}: {e}")
            return False
