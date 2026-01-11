"""
Soundboard export utilities.

This module handles the creation of soundboard packs (ZIP archives), including
manifest generation and asset packaging.
"""

import io
import json
import os
import zipfile
from typing import Any, Dict, Optional

from flask import current_app

from app.models import Sound, Soundboard


class Packager:
    """Handles the logic for exporting soundboards."""

    @staticmethod
    def create_soundboard_pack(soundboard: Soundboard) -> io.BytesIO:
        """
        Create a ZIP archive containing the soundboard manifest and all associated assets.

        Args:
            soundboard (Soundboard): The soundboard object to export.

        Returns:
            BytesIO: A BytesIO object containing the ZIP data.
        """
        memory_file = io.BytesIO()

        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Initialize Manifest
            manifest = Packager._build_manifest_base(soundboard)

            # 2. Package Sounds and their icons
            Packager._package_sounds(zf, soundboard, manifest)

            # 3. Package Board Icon
            Packager._package_board_icon(zf, soundboard, manifest)

            # 4. Finalize: Write manifest to zip
            zf.writestr("manifest.json", json.dumps(manifest, indent=4))

        memory_file.seek(0)
        return memory_file

    @staticmethod
    def _build_manifest_base(sb: Soundboard) -> Dict[str, Any]:
        """Build the basic structure of the manifest."""
        return {
            "version": "1.0",
            "name": sb.name,
            "icon": sb.icon if not (sb.icon and "/" in sb.icon) else None,
            "theme_color": sb.theme_color,
            "tags": [t.name for t in sb.get_tags()],
            "sounds": [],
        }

    @staticmethod
    def _package_sounds(zf: zipfile.ZipFile, sb: Soundboard, manifest: Dict) -> None:
        """Iterate through sounds and add them to the package."""
        for sound in sb.get_sounds():
            if not sound.file_path:
                continue

            sound_data = Packager._package_single_sound(zf, sound)
            if sound_data:
                manifest["sounds"].append(sound_data)

    @staticmethod
    def _package_single_sound(zf: zipfile.ZipFile, sound: Sound) -> Optional[Dict]:
        """Package a single sound file and its custom icon if present."""
        full_audio_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], sound.file_path
        )
        if not os.path.exists(full_audio_path):
            return None

        file_name = os.path.basename(sound.file_path)
        sound_data = {
            "name": sound.name,
            "file_name": file_name,
            "icon": sound.icon if not (sound.icon and "/" in sound.icon) else None,
            "display_order": sound.display_order,
            "volume": sound.volume,
            "is_loop": sound.is_loop,
            "start_time": sound.start_time,
            "end_time": sound.end_time,
            "hotkey": sound.hotkey,
        }

        # Add audio file to zip
        zf.write(full_audio_path, arcname=f"sounds/{file_name}")

        # Add custom sound icon if it's a file
        if sound.icon and "/" in sound.icon:
            full_icon_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], sound.icon
            )
            if os.path.exists(full_icon_path):
                zip_icon_path = f"icons/{os.path.basename(sound.icon)}"
                zf.write(full_icon_path, arcname=zip_icon_path)
                sound_data["custom_icon_file"] = zip_icon_path

        return sound_data

    @staticmethod
    def _package_board_icon(
        zf: zipfile.ZipFile, sb: Soundboard, manifest: Dict
    ) -> None:
        """Package the board's custom icon if it exists."""
        if not (sb.icon and "/" in sb.icon):
            return

        full_board_icon_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], sb.icon
        )
        if os.path.exists(full_board_icon_path):
            zip_board_icon_path = f"icons/board_{os.path.basename(sb.icon)}"
            zf.write(full_board_icon_path, arcname=zip_board_icon_path)
            manifest["custom_board_icon_file"] = zip_board_icon_path
