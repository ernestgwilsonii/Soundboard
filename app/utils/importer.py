"""
Soundboard import utilities.

This module handles the importing of soundboard packs (ZIP archives), including
validating manifests and reconstructing database records.
"""

import json
import os
import uuid
import zipfile
from typing import BinaryIO, Dict, Tuple

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
            Exception: For other errors during import.
        """
        try:
            with zipfile.ZipFile(zip_stream, "r") as zf:
                manifest = Importer._extract_manifest(zf)
                new_sb = Importer._create_soundboard(manifest, user_id)

                Importer._handle_custom_board_icon(zf, manifest, new_sb)
                Importer._process_tags(manifest, new_sb)
                Importer._process_sounds(zf, manifest, new_sb)

                return new_sb

        except Exception as e:
            current_app.logger.error(f"Import failed: {e}")
            raise e

    @staticmethod
    def _extract_manifest(zf: zipfile.ZipFile) -> Dict:
        """Extract and validate the manifest from the ZIP file."""
        if "manifest.json" not in zf.namelist():
            raise ValueError("Invalid pack: manifest.json missing")

        manifest_data = zf.read("manifest.json")
        return json.loads(manifest_data)

    @staticmethod
    def _create_soundboard(manifest: Dict, user_id: int) -> Soundboard:
        """Create the initial Soundboard record from manifest data."""
        sb_name = f"{manifest.get('name', 'Imported Board')} (Imported)"
        sb_icon = manifest.get("icon", DEFAULT_SOUNDBOARD_ICON)
        theme_color = manifest.get("theme_color", DEFAULT_SOUNDBOARD_COLOR)

        new_sb = Soundboard(
            name=sb_name,
            user_id=user_id,
            icon=sb_icon,
            is_public=False,
            theme_color=theme_color,
        )
        new_sb.save()
        return new_sb

    @staticmethod
    def _handle_custom_board_icon(
        zf: zipfile.ZipFile, manifest: Dict, sb: Soundboard
    ) -> None:
        """Process and save the custom board icon if present."""
        if "custom_board_icon_file" not in manifest:
            return

        icon_path_in_zip = manifest["custom_board_icon_file"]
        if icon_path_in_zip not in zf.namelist():
            return

        ext = os.path.splitext(icon_path_in_zip)[1]
        new_icon_name = f"icons/board_{sb.id}_{uuid.uuid4().hex}{ext}"
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], new_icon_name)

        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        with open(full_path, "wb") as f:
            f.write(zf.read(icon_path_in_zip))

        sb.icon = new_icon_name
        sb.save()

    @staticmethod
    def _process_tags(manifest: Dict, sb: Soundboard) -> None:
        """Add tags from the manifest to the soundboard."""
        for tag_name in manifest.get("tags", []):
            sb.add_tag(tag_name)

    @staticmethod
    def _process_sounds(zf: zipfile.ZipFile, manifest: Dict, sb: Soundboard) -> None:
        """Process all sounds defined in the manifest."""
        sb_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(sb.id))
        if not os.path.exists(sb_dir):
            os.makedirs(sb_dir)

        for s_data in manifest.get("sounds", []):
            Importer._process_single_sound(zf, s_data, sb)

    @staticmethod
    def _process_single_sound(
        zf: zipfile.ZipFile, s_data: Dict, sb: Soundboard
    ) -> None:
        """Extract, process, and save a single sound and its icon."""
        zip_audio_path = f"sounds/{s_data['file_name']}"
        if zip_audio_path not in zf.namelist():
            return

        audio_path = Importer._save_audio_file(zf, s_data, sb)
        sound_icon = Importer._get_sound_icon(zf, s_data)
        Importer._create_sound_record(sb, s_data, audio_path, sound_icon)

    @staticmethod
    def _save_audio_file(zf: zipfile.ZipFile, s_data: Dict, sb: Soundboard) -> str:
        """Process and save the audio file to disk."""
        zip_audio_path = f"sounds/{s_data['file_name']}"
        audio_bytes = zf.read(zip_audio_path)
        processed_bytes, processed_name = AudioProcessor.process_audio(
            audio_bytes, s_data["file_name"]
        )

        unique_filename = f"{uuid.uuid4().hex}_{processed_name}"
        audio_path = os.path.join(str(sb.id), unique_filename)
        full_audio_path = os.path.join(current_app.config["UPLOAD_FOLDER"], audio_path)

        with open(full_audio_path, "wb") as f:
            f.write(processed_bytes)

        return audio_path

    @staticmethod
    def _create_sound_record(
        sb: Soundboard, s_data: Dict, audio_path: str, sound_icon: str
    ) -> Sound:
        """Create and save the Sound database record."""
        new_sound = Sound(
            soundboard_id=sb.id,
            name=s_data["name"],
            file_path=audio_path,
            icon=sound_icon,
            display_order=s_data.get("display_order", 0),
            volume=s_data.get("volume", 1.0),
            is_loop=s_data.get("is_loop", False),
            start_time=s_data.get("start_time", 0.0),
            end_time=s_data.get("end_time"),
        )
        new_sound.save()
        return new_sound

    @staticmethod
    def _get_sound_icon(zf: zipfile.ZipFile, s_data: Dict) -> str:
        """Determine and save the sound icon (custom or default)."""
        default_icon = s_data.get("icon", DEFAULT_SOUND_ICON)

        if "custom_icon_file" not in s_data:
            return default_icon

        zip_s_icon_path = s_data["custom_icon_file"]
        if zip_s_icon_path not in zf.namelist():
            return default_icon

        ext = os.path.splitext(zip_s_icon_path)[1]
        new_s_icon_name = f"icons/sound_{uuid.uuid4().hex}{ext}"
        full_s_icon_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], new_s_icon_name
        )

        if not os.path.exists(os.path.dirname(full_s_icon_path)):
            os.makedirs(os.path.dirname(full_s_icon_path))

        with open(full_s_icon_path, "wb") as f:
            f.write(zf.read(zip_s_icon_path))

        return new_s_icon_name
