"""
File storage utilities.

This module handles file system operations for uploading and managing files,
ensuring secure paths and proper directory structures.
"""

import os
import uuid
from typing import Optional

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class Storage:
    """Handles file storage operations."""

    @staticmethod
    def save_file(
        file: FileStorage,
        subfolder: str = "",
        custom_filename: Optional[str] = None,
        use_uuid: bool = False,
    ) -> str:
        """
        Save an uploaded file to the configured upload folder.

        Args:
            file (FileStorage): The uploaded file object.
            subfolder (str, optional): Subdirectory within the upload folder. Defaults to "".
            custom_filename (str, optional): Override the original filename.
            use_uuid (bool, optional): Prepend a UUID to the filename to avoid collisions.

        Returns:
            str: The relative path to the saved file.

        Raises:
            ValueError: If the file is invalid.
        """
        if not file or not file.filename:
            raise ValueError("No file provided")

        original_filename = secure_filename(file.filename)
        filename = custom_filename if custom_filename else original_filename

        if use_uuid:
            filename = f"{uuid.uuid4().hex}_{filename}"

        # Ensure unique filename if collision occurs and UUID wasn't requested
        if not use_uuid:
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(
                os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder, filename)
            ):
                filename = f"{base}_{counter}{ext}"
                counter += 1

        relative_path = os.path.join(subfolder, filename)
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], relative_path)

        # Create directory if it doesn't exist
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        file.save(full_path)
        return relative_path

    @staticmethod
    def get_full_path(relative_path: str) -> str:
        """
        Get the absolute filesystem path for a stored file.

        Args:
            relative_path (str): The relative path from the upload folder.

        Returns:
            str: The absolute path.
        """
        return os.path.join(current_app.config["UPLOAD_FOLDER"], relative_path)

    @staticmethod
    def delete_file(relative_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            relative_path (str): The relative path to the file.

        Returns:
            bool: True if deleted or didn't exist, False on error.
        """
        full_path = Storage.get_full_path(relative_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
            return True
        except Exception:
            current_app.logger.exception(f"Failed to delete file: {relative_path}")
            return False
