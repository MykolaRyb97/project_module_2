import uuid
import io
import os
import math
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
    file_path = config.IMAGE_DIR/unique_name

    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)

    return {
        "filename": unique_name,
        "url": f"/images/{unique_name}"
    }
def get_uploaded_images(page: int = 1, per_page: int = 8, order: str = "desc") -> dict:
    """
    Return paginated list of uploaded images in format expected by frontend:
    {
      "items": [{"filename": "...", "url": "/images/..."}],
      "pagination": {"total": N, "pages": P, "page": page, "per_page": per_page, "order": order}
    }
    """
    images_dir = config.IMAGE_DIR

    # створюємо директорію, якщо її ще нема
    os.makedirs(images_dir, exist_ok=True)

    files = [
        f for f in os.listdir(images_dir)
        if os.path.isfile(os.path.join(images_dir, f))
        and os.path.splitext(f)[1].lower() in config.SUPPORTED_FORMATS
    ]

    # сортування за часом модифікації (новіші/старіші)
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
