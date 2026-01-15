"""
Soundboard import utilities.

This module handles the importing of soundboard packs (ZIP archives), including
validating manifests and reconstructing database records.
"""

import json
import os
import uuid
import zipfile
from typing import Any, BinaryIO, Dict, Tuple, cast

from flask import current_app

from app.constants import (
    DEFAULT_SOUND_ICON,
    DEFAULT_SOUNDBOARD_COLOR,
    DEFAULT_SOUNDBOARD_ICON,
)
from app.models import Sound, Soundboard


class AudioProcessor:
    """Placeholder for audio processing during import."""

    @staticmethod
    def process_audio(file_bytes: bytes, filename: str) -> Tuple[bytes, str]:
        """
        Process audio bytes (placeholder).

        Args:
            file_bytes (bytes): The audio file content.
            filename (str): The original filename.

        Returns:
            tuple: (processed_bytes, filename)
        """
        return file_bytes, filename


class Importer:
    """Handles the logic for importing soundboard packs."""

    @staticmethod
    def import_soundboard_pack(zip_stream: BinaryIO, user_id: int) -> Soundboard:
        """
        Extract a Soundboard Pack and reconstruct the soundboard in the database.

        Args:
            zip_stream (file-like): The ZIP file stream.
            user_id (int): The ID of the user importing the board.

        Returns:
            Soundboard: The newly created Soundboard object.

        Raises:
            ValueError: If the pack is invalid (e.g., missing manifest).
            zipfile.BadZipFile: If the provided stream is not a valid ZIP.
            Exception: For other unexpected errors during import.
        """
        try:
            with zipfile.ZipFile(zip_stream, "r") as zip_file:
                manifest = Importer._extract_manifest(zip_file)
                new_soundboard = Importer._create_soundboard(manifest, user_id)

                Importer._handle_custom_board_icon(zip_file, manifest, new_soundboard)
                Importer._process_tags(manifest, new_soundboard)
                Importer._process_sounds(zip_file, manifest, new_soundboard)

                return new_soundboard

        except (zipfile.BadZipFile, ValueError) as e:
            current_app.logger.warning(f"Invalid soundboard pack: {e}")
            raise
        except Exception:
            current_app.logger.exception("Unexpected failure during soundboard import")
            raise

    @staticmethod
    def _extract_manifest(zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """Extract and validate the manifest from the ZIP file."""
        if "manifest.json" not in zip_file.namelist():
            raise ValueError("Invalid pack: manifest.json missing")

        manifest_data = zip_file.read("manifest.json")
        return cast(Dict[str, Any], json.loads(manifest_data))

    @staticmethod
    def _create_soundboard(manifest: Dict[str, Any], user_id: int) -> Soundboard:
        """Create the initial Soundboard record from manifest data."""
        soundboard_name = f"{manifest.get('name', 'Imported Board')} (Imported)"
        soundboard_icon = manifest.get("icon", DEFAULT_SOUNDBOARD_ICON)
        theme_color = manifest.get("theme_color", DEFAULT_SOUNDBOARD_COLOR)

        new_soundboard = Soundboard(
            name=soundboard_name,
            user_id=user_id,
            icon=soundboard_icon,
            is_public=False,
            theme_color=theme_color,
        )
        new_soundboard.save()
        return new_soundboard

    @staticmethod
    def _handle_custom_board_icon(
        zip_file: zipfile.ZipFile, manifest: Dict[str, Any], soundboard: Soundboard
    ) -> None:
        """Process and save the custom board icon if present."""
        if "custom_board_icon_file" not in manifest:
            return

        icon_path_in_zip = manifest["custom_board_icon_file"]
        if icon_path_in_zip not in zip_file.namelist():
            return

        ext = os.path.splitext(icon_path_in_zip)[1]
        new_icon_name = f"icons/board_{soundboard.id}_{uuid.uuid4().hex}{ext}"
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], new_icon_name)

        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        with open(full_path, "wb") as icon_file:
            icon_file.write(zip_file.read(icon_path_in_zip))

        soundboard.icon = new_icon_name
        soundboard.save()

    @staticmethod
    def _process_tags(manifest: Dict[str, Any], soundboard: Soundboard) -> None:
        """Add tags from the manifest to the soundboard."""
        for tag_name in manifest.get("tags", []):
            soundboard.add_tag(tag_name)

    @staticmethod
    def _process_sounds(
        zip_file: zipfile.ZipFile, manifest: Dict[str, Any], soundboard: Soundboard
    ) -> None:
        """Process all sounds defined in the manifest."""
        soundboard_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], str(soundboard.id)
        )
        if not os.path.exists(soundboard_dir):
            os.makedirs(soundboard_dir)

        for sound_data in manifest.get("sounds", []):
            Importer._process_single_sound(zip_file, sound_data, soundboard)

    @staticmethod
    def _process_single_sound(
        zip_file: zipfile.ZipFile, sound_data: Dict[str, Any], soundboard: Soundboard
    ) -> None:
        """Extract, process, and save a single sound and its icon."""
        zip_audio_path = f"sounds/{sound_data['file_name']}"
        if zip_audio_path not in zip_file.namelist():
            return

        audio_path = Importer._save_audio_file(zip_file, sound_data, soundboard)
        sound_icon = Importer._get_sound_icon(zip_file, sound_data)
        Importer._create_sound_record(soundboard, sound_data, audio_path, sound_icon)

    @staticmethod
    def _save_audio_file(
        zip_file: zipfile.ZipFile, sound_data: Dict[str, Any], soundboard: Soundboard
    ) -> str:
        """Process and save the audio file to disk."""
        zip_audio_path = f"sounds/{sound_data['file_name']}"
        audio_bytes = zip_file.read(zip_audio_path)
        processed_bytes, processed_name = AudioProcessor.process_audio(
            audio_bytes, sound_data["file_name"]
        )

        unique_filename = f"{uuid.uuid4().hex}_{processed_name}"
        audio_path = os.path.join(str(soundboard.id), unique_filename)
        full_audio_path = os.path.join(current_app.config["UPLOAD_FOLDER"], audio_path)

        with open(full_audio_path, "wb") as audio_file:
            audio_file.write(processed_bytes)

        return audio_path

    @staticmethod
    def _create_sound_record(
        soundboard: Soundboard,
        sound_data: Dict[str, Any],
        audio_path: str,
        sound_icon: str,
    ) -> Sound:
        """Create and save the Sound database record."""
        new_sound = Sound(
            soundboard_id=soundboard.id,
            name=sound_data["name"],
            file_path=audio_path,
            icon=sound_icon,
            display_order=sound_data.get("display_order", 0),
            volume=sound_data.get("volume", 1.0),
            is_loop=sound_data.get("is_loop", False),
            start_time=sound_data.get("start_time", 0.0),
            end_time=sound_data.get("end_time"),
        )
        new_sound.save()
        return new_sound

    @staticmethod
    def _get_sound_icon(zip_file: zipfile.ZipFile, sound_data: Dict[str, Any]) -> str:
        """Determine and save the sound icon (custom or default)."""
        default_icon = str(sound_data.get("icon", DEFAULT_SOUND_ICON))

        if "custom_icon_file" not in sound_data:
            return default_icon

        zip_sound_icon_path = sound_data["custom_icon_file"]
        if zip_sound_icon_path not in zip_file.namelist():
            return default_icon

        ext = os.path.splitext(zip_sound_icon_path)[1]
        new_sound_icon_name = f"icons/sound_{uuid.uuid4().hex}{ext}"
        full_sound_icon_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], new_sound_icon_name
        )

        if not os.path.exists(os.path.dirname(full_sound_icon_path)):
            os.makedirs(os.path.dirname(full_sound_icon_path))

        with open(full_sound_icon_path, "wb") as icon_file:
            icon_file.write(zip_file.read(zip_sound_icon_path))

        return new_sound_icon_name
