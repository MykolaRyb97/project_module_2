import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request



from settings.config import config
from settings.logging_config import get_logger
from handlers.files import list_uploaded_images
from handlers.upload import handle_uploaded_file
from exceptions.api_errors import APIError, MultipleFilesUploadError


logger = get_logger(__name__)

app = FastAPI(title="Upload Server")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    logger.error(f"{request.method} {request.url.path} → {exc.status_code}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


# -------------------------------------------------------------
# GET /
# -------------------------------------------------------------
@app.get("/")
async def root():
    logger.info("Healthcheck endpoint hit: /")
    return {"message": "Welcome to the Upload Server"}


# -------------------------------------------------------------
# GET /upload/
# -------------------------------------------------------------
@app.get("/upload/")
async def get_uploads():
    try:
        files = list_uploaded_images()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Images directory not found.")
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied.")

    if not files:
        raise HTTPException(status_code=404, detail="No images found.")

    return files


# -------------------------------------------------------------
# POST /upload/
# -------------------------------------------------------------
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        saved_info = handle_uploaded_file(file)
    except MultipleFilesUploadError:
        raise HTTPException(status_code=400, detail="Only one file allowed.")
    except APIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    logger.info(f"File '{saved_info['filename']}' uploaded successfully.")
    return saved_info



# -------------------------------------------------------------
# DELETE /upload/{filename}
# -------------------------------------------------------------
@app.delete("/upload/{filename}")
async def delete_upload(filename: str):
    ext = os.path.splitext(filename)[1].lower()

    if ext not in config.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    filepath = os.path.join(config.IMAGE_DIR, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        os.remove(filepath)
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied to delete file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return {"message": f"File '{filename}' deleted successfully."}



