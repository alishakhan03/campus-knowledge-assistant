import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_EXTENSION = ".pdf"
ALLOWED_MIME_TYPES = {"application/pdf"}


def safe_filename(original_name: str) -> str:
    """Never trust the original filename - generate a random server-side name."""
    return f"{uuid.uuid4().hex}{ALLOWED_EXTENSION}"


def validate_pdf_upload(file: UploadFile, content: bytes) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext != ALLOWED_EXTENSION:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid file type; expected application/pdf")

    if len(content) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )


def save_upload(content: bytes, filename: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path
