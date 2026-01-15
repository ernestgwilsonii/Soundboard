"""
Audio processing utilities.

This module provides functionality for extracting metadata from audio files
and performing normalization.
"""

import logging
import os
from typing import Any, Dict, Optional, cast

import mutagen
from pydub import AudioSegment

from app.constants import NORMALIZATION_TARGET_DBFS

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio file processing tasks."""

    @staticmethod
    def get_metadata(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from an audio file.

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

            return AudioProcessor._build_metadata_dict(audio, file_path)
        except (mutagen.MutagenError, FileNotFoundError):
            logger.warning(f"Could not read audio file at {file_path}")
            return None
        except Exception:
            logger.exception(
                f"Unexpected error processing audio metadata for {file_path}"
            )
            return None

    @staticmethod
    def _build_metadata_dict(audio: Any, file_path: str) -> Dict[str, Any]:
        """Construct the metadata dictionary from mutagen object."""
        return {
            "duration": round(audio.info.length, 3),
            "sample_rate": getattr(audio.info, "sample_rate", 0),
            "bitrate": AudioProcessor._extract_bitrate(audio.info),
            "file_size": os.path.getsize(file_path),
            "format": type(audio).__name__,
        }

    @staticmethod
    def _extract_bitrate(info: Any) -> int:
        """Extract bitrate in kbps from mutagen info object."""
        if hasattr(info, "bitrate") and info.bitrate:
            return cast(int, info.bitrate // 1000)
        return 0

    @staticmethod
    def normalize(
        file_path: str, target_dbfs: float = NORMALIZATION_TARGET_DBFS
    ) -> bool:
        """
        Normalize the volume of an audio file.

        Args:
            file_path (str): The path to the audio file.
            target_dbfs (float, optional): The target volume level. Defaults to NORMALIZATION_TARGET_DBFS.
        """
        try:
            audio = AudioSegment.from_file(file_path)
            change_in_dbfs = target_dbfs - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dbfs)

            format_ext = AudioProcessor._get_export_format(file_path)

            normalized_audio.export(file_path, format=format_ext)
            logger.info(f"Normalized {file_path} to {target_dbfs} dBFS")
            return True
        except FileNotFoundError:
            logger.error(f"Audio file not found for normalization: {file_path}")
            return False
        except Exception:
            logger.exception(f"Unexpected error normalizing audio for {file_path}")
            return False

    @staticmethod
    def _get_export_format(file_path: str) -> str:
        """Determine the export format from file extension."""
        ext = os.path.splitext(file_path)[1][1:].lower()
        if ext == "sbp":  # Soundboard Pack file extension
            return "zip"
        return ext
