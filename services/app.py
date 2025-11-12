import os
import uuid
import shutil
import json
from datetime import datetime, UTC

from backend.settings.config import config

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from PIL import Image

app = FastAPI(title="Upload Server", description="Simple file upload service")

os.makedirs(config.IMAGE_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=config.IMAGE_DIR), name="images")


@app.get("/")
async def root():
    return {"message": "Welcome to the Upload Server"}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in config.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Allowed: {config.SUPPORTED_FORMATS}")

    contents = await file.read()

    # image = Image.open(io.BytesIO(contents))
    # w, h = image.size
    # ascpect_ratio = w / h
    # 1920x1080 - 16:9
    # 800x1200 - 2:3

    # w > h - горз

    size = len(contents)
    if size > config.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {config.MAX_FILE_SIZE} bytes")

    base = os.path.splitext(filename)[0]
    safe_base = "".join(c if c.isalnum() or c in "._-" else "_" for c in base).lower()
    unique_name = f"{safe_base}_{uuid.uuid4()}{ext}"
    file_path = os.path.join(config.IMAGES_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    return {"filename": unique_name, "url": f"/images/{unique_name}"}


@app.get("/upload/")
async def list_files():
    try:
        filenames = os.listdir(config.IMAGES_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Images directory not found.")

    files = []
    for filename in filenames:
        filepath = os.path.join(config.IMAGES_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext in config.SUPPORTED_FORMATS and os.path.isfile(filepath):
            created_at = datetime.fromtimestamp(os.path.getctime(filepath), tz=UTC).isoformat()
            size = os.path.getsize(filepath)
            files.append({
                "filename": filename,
                "created_at": created_at,
                "size": size,
                "url": f"/images/{filename}"
            })

    return files
