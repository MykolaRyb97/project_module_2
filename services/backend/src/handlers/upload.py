import uuid
import io
import os
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from settings.config import config
from exceptions.api_errors import (
    NotSupportedFormatError,
    MaxSizeExceedError
)

def handle_uploaded_file(upload_file: UploadFile) -> dict[str, str]:
    filename = upload_file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in config.SUPPORTED_FORMATS:
        raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

    # Read contents
    contents = upload_file.file.read()
    size = len(contents)

    if size > config.MAX_FILE_SIZE:
        raise MaxSizeExceedError(config.MAX_FILE_SIZE)

    # Validate image
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
    except (UnidentifiedImageError, OSError):
        raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

    # Generate unique filename
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = config.IMAGE_DIR / unique_name

    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)

    return {
        "filename": unique_name,
        "url": f"/images/{unique_name}"
    }
