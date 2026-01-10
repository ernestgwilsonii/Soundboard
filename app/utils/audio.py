"""
Audio processing utilities.

This module provides functionality for extracting metadata from audio files
and performing normalization.
"""

import logging
import os
from typing import Any, Dict, Optional

import mutagen
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio file processing tasks."""

    @staticmethod
    def get_metadata(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata (duration, sample_rate, bitrate, file_size, format) from an audio file.

        Args:
            file_path (str): The path to the audio file.

        Returns:
            dict or None: A dictionary containing metadata, or None if extraction fails.
        """
        try:
            audio = mutagen.File(file_path)
            if audio is None or not audio.info:
                logger.warning(f"Could not read metadata from {file_path}")
                return None

            return {
                "duration": round(audio.info.length, 3),
                "sample_rate": getattr(audio.info, "sample_rate", 0),
                "bitrate": (
                    getattr(audio.info, "bitrate", 0) // 1000
                    if hasattr(audio.info, "bitrate")
                    else 0
                ),
                "file_size": os.path.getsize(file_path),
                "format": type(audio).__name__,
            }
        except Exception as e:
            logger.error(f"Error processing audio metadata for {file_path}: {e}")
            return None

    @staticmethod
    def normalize(file_path: str, target_dbfs: float = -20.0) -> bool:
        """
        Normalize the audio volume to a target dBFS level.

        This method overwrites the original file with the normalized version.

        Args:
            file_path (str): The path to the audio file.
            target_dbfs (float, optional): The target volume level. Defaults to -20.0.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            audio = AudioSegment.from_file(file_path)
            change_in_dbfs = target_dbfs - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dbfs)

            # Determine format from extension
            ext = os.path.splitext(file_path)[1][1:].lower()
            if ext == "sbp":  # Should not happen here but safety first
                ext = "zip"

            normalized_audio.export(file_path, format=ext)
            logger.info(f"Normalized {file_path} to {target_dbfs} dBFS")
            return True
        except Exception as e:
            logger.error(f"Error normalizing audio for {file_path}: {e}")
            return False
