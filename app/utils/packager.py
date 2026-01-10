"""
Soundboard export utilities.

This module handles the creation of soundboard packs (ZIP archives), including
manifest generation and asset packaging.
"""

import io
import json
import os
import zipfile
from typing import Any, Dict

from flask import current_app

from app.models import Soundboard


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
            # 1. Generate Manifest
            manifest: Dict[str, Any] = {
                "version": "1.0",
                "name": soundboard.name,
                "icon": (
                    soundboard.icon
                    if not (soundboard.icon and "/" in soundboard.icon)
                    else None
                ),
                "theme_color": soundboard.theme_color,
                "tags": [t.name for t in soundboard.get_tags()],
                "sounds": [],
            }

            # 2. Add Sounds and their assets
            for sound in soundboard.get_sounds():
                if not sound.file_path:
                    continue

                sound_data: Dict[str, Any] = {
                    "name": sound.name,
                    "file_name": os.path.basename(sound.file_path),
                    "icon": (
                        sound.icon if not (sound.icon and "/" in sound.icon) else None
                    ),
                    "display_order": sound.display_order,
                    "volume": sound.volume,
                    "is_loop": sound.is_loop,
                    "start_time": sound.start_time,
                    "end_time": sound.end_time,
                    "hotkey": sound.hotkey,
                }

                # Add audio file to zip
                full_audio_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], sound.file_path
                )
                if os.path.exists(full_audio_path):
                    zf.write(
                        full_audio_path, arcname=f"sounds/{sound_data['file_name']}"
                    )
                    manifest["sounds"].append(sound_data)

                # Add custom sound icon if it's a file
                if sound.icon and "/" in sound.icon:
                    full_icon_path = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], sound.icon
                    )
                    if os.path.exists(full_icon_path):
                        zip_icon_path = f"icons/{os.path.basename(sound.icon)}"
                        zf.write(full_icon_path, arcname=zip_icon_path)
                        # Store the relative path within the zip in the sound_data
                        sound_data["custom_icon_file"] = zip_icon_path

            # Add custom board icon if it's a file
            if soundboard.icon and "/" in soundboard.icon:
                full_board_icon_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], soundboard.icon
                )
                if os.path.exists(full_board_icon_path):
                    zip_board_icon_path = (
                        f"icons/board_{os.path.basename(soundboard.icon)}"
                    )
                    zf.write(full_board_icon_path, arcname=zip_board_icon_path)
                    manifest["custom_board_icon_file"] = zip_board_icon_path

            # Write manifest to zip
            zf.writestr("manifest.json", json.dumps(manifest, indent=4))

        memory_file.seek(0)
        return memory_file
