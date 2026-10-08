import re
import secrets
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.features.media_library.models import MediaFile

ALLOWED_MIME_PREFIXES = ("image/", "video/")
ALLOWED_MIME_EXACT = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
}

EXT_RE = re.compile(r"[^A-Za-z0-9._-]")


def _new_public_id() -> str:
    return str(uuid.uuid4())


def _safe_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    ext = filename.rsplit(".", 1)[1].lower()
    ext = EXT_RE.sub("", ext)[:10]
    return f".{ext}" if ext else ""


def _is_allowed(mime: str) -> bool:
    if mime in ALLOWED_MIME_EXACT:
        return True
    return any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES)


def _ensure_upload_dir() -> Path:
    p = settings.upload_path
    p.mkdir(parents=True, exist_ok=True)
    return p


async def save_upload(
    db: Session,
    *,
    file: UploadFile,
    admin_id: int | None,
    base_url: str,
) -> MediaFile:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    mime = file.content_type or "application/octet-stream"
    if not _is_allowed(mime):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {mime}",
        )

    upload_dir = _ensure_upload_dir()

    ext = _safe_extension(file.filename)
    stored_filename = f"{secrets.token_hex(16)}{ext}"
    dest = upload_dir / stored_filename

    max_bytes = settings.max_upload_bytes
    size = 0
    chunk_size = 1024 * 1024

    try:
        with dest.open("wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB} MB.",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to save file")

    base = base_url.rstrip("/")
    url = f"{base}/uploads/{stored_filename}"

    media = MediaFile(
        public_id=_new_public_id(),
        original_filename=file.filename[:255],
        stored_filename=stored_filename,
        url=url,
        mime_type=mime[:120],
        size_bytes=size,
        uploaded_by_admin_id=admin_id,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def list_media(
    db: Session, *, limit: int = 50, offset: int = 0
) -> tuple[list[MediaFile], int]:
    query = db.query(MediaFile)
    total = query.with_entities(func.count(MediaFile.id)).scalar() or 0
    items = (
        query.order_by(MediaFile.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def get_media(db: Session, media_id: int) -> MediaFile:
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


def delete_media(db: Session, media_id: int) -> None:
    media = get_media(db, media_id)
    path = _ensure_upload_dir() / media.stored_filename
    path.unlink(missing_ok=True)
    db.delete(media)
    db.commit()