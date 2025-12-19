"""File service module for managing image files.

This module provides a service class to handle the full lifecycle of image files:
- Validating uploaded files (format, size, integrity)
- Saving files with unique names
- Retrieving file information
- Deleting files

Abstracts file operations away from the HTTP layer, making the code more testable
and maintainable.
"""

import os
import uuid
import shutil
import math
from typing import cast, List, Callable, Any

from PIL import Image, UnidentifiedImageError

from dto.file import UploadedFileDTO
from settings.config import config
from exceptions.api_errors import (
    NotSupportedFormatError,
    MaxSizeExceedError,
    MultipleFilesUploadError,
    UnsupportedFileFormatError,
    PermissionDeniedError,
    FileNotFoundError,
    APIError
)
from interfaces.protocols import SupportsWrite
from interfaces.handlers import FileHandlerInterface



class FileHandler(FileHandlerInterface):
    """Service for managing image files throughout their lifecycle.

    This class abstracts the file operations from the HTTP handlers,
    providing a clean interface for file validation, storage, and retrieval.

    Attributes:
        _images_dir: Directory where image files are stored.
        _max_file_size: Maximum allowed file size in bytes.
        _supported_formats: List of allowed file extensions.
    """

    def __init__(
            self,
            images_dir: str = config.IMAGE_DIR,
            max_file_size: int = config.MAX_FILE_SIZE,
            supported_formats: set[str] = config.SUPPORTED_FORMATS
    ):
        """Initialize the FileService with configuration.

        Args:
            images_dir: Directory where image files are stored.
            max_file_size: Maximum allowed file size in bytes.
            supported_formats: List of allowed file extensions.
        """
        self._images_dir = images_dir
        self._max_file_size = max_file_size
        self._supported_formats = supported_formats

    def handle_upload(self, file) -> UploadedFileDTO:
        """Validates and saves a single uploaded image file to disk.

        Args:
            file: A multipart-compatible file-like object containing:
                - file_name (bytes | None): The name of the uploaded file.
                - file_object (IO[bytes]): The binary file stream.

        Returns:
            UploadedFileDTO: Data transfer object containing information about the saved file.

        Raises:
            NotSupportedFormatError: If the file extension or content is invalid.
            MaxSizeExceedError: If the file exceeds the configured size limit.
        """
        filename = file.file_name.decode("utf-8") if file.file_name else "uploaded_file"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in self._supported_formats:
            raise NotSupportedFormatError(self._supported_formats)

        file.file_object.seek(0, os.SEEK_END)
        size = file.file_object.tell()
        file.file_object.seek(0)

        if size > self._max_file_size:
            raise MaxSizeExceedError(self._max_file_size)

        try:
            image = Image.open(file.file_object)
            image.verify()
            file.file_object.seek(0)
        except (UnidentifiedImageError, OSError):
            raise NotSupportedFormatError(self._supported_formats)

        original_name = os.path.splitext(filename)[0].lower()
        original_name = ''.join(c for c in original_name if c.isalnum() or c in '_-')[:50]
        unique_name = f"{original_name}_{uuid.uuid4()}{ext}"
        file_path = os.path.join(self._images_dir, unique_name)

        with open(file_path, "wb") as f:
            file.file_object.seek(0)
            shutil.copyfileobj(file.file_object, cast(SupportsWrite, f))

        return UploadedFileDTO(
            filename=unique_name,
            original_name=filename,
            size=size,
            extension=ext,
            url=f"/images/{unique_name}"
        )

    def get_file_collector(self, files_list: List) -> Callable[[Any], None]:
        """Returns a callback function that collects files into the provided list.

        Creates a closure that has access to the files_list and implements
        logic for handling file collection during multipart form parsing.

        Args:
            files_list: A list where uploaded files will be collected.

        Returns:
            A callback function to be used with multipart form parser.

        Raises:
            MultipleFilesUploadError: If more than one file is being uploaded.
        """

        def on_file(file):
            if len(files_list) >= 1:
                raise MultipleFilesUploadError()
            files_list.append(file)

        return on_file

    def delete_file(self, filename: str) -> None:
        """Delete a file from the file system.

        Args:
            filename: The name of the file to delete.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnsupportedFileFormatError: If the file has an unsupported extension.
            PermissionDeniedError: If there are permission issues deleting the file.
            APIError: For other errors that may occur during deletion.
        """
        filepath = os.path.join(self._images_dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in self._supported_formats:
            raise UnsupportedFileFormatError(ext, self._supported_formats)

        if not os.path.isfile(filepath):
            raise FileNotFoundError(filename)

        try:
            os.remove(filepath)
        except PermissionError:
            raise PermissionDeniedError("delete file")
        except Exception as e:
            raise APIError(f"Failed to delete file: {str(e)}")

def list_uploaded_images(page: int = 1, per_page: int = 8, order: str = "desc") -> dict:
    """
    Повертає список картинок у форматі, який очікує фронт:
    {
      "items": [{"filename": "...", "url": "/images/..."}],
      "pagination": {"total": N, "pages": P, "page": page, "per_page": per_page, "order": order}
    }
    """
    images_dir = config.IMAGE_DIR
    os.makedirs(images_dir, exist_ok=True)

    files = [
        f for f in os.listdir(images_dir)
        if os.path.isfile(os.path.join(images_dir, f))
        and os.path.splitext(f)[1].lower() in config.SUPPORTED_FORMATS
    ]

    # сортування: asc = старіші → новіші, desc = новіші → старіші
    files.sort(
        key=lambda fn: os.path.getmtime(os.path.join(images_dir, fn)),
        reverse=(order != "asc"),
    )

    total = len(files)
    pages = max(1, math.ceil(total / per_page)) if total else 1

    start = (page - 1) * per_page
    end = start + per_page
    slice_files = files[start:end] if start < total else []

    items = [{"filename": fn, "url": f"/images/{fn}"} for fn in slice_files]

    return {
        "items": items,
        "pagination": {
            "total": total,
            "pages": pages,
            "page": page,
            "per_page": per_page,
            "order": order,
        },
    }