from pathlib import Path
from urllib.parse import urlsplit
from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session
from app.features.media_library.models import MediaFile
from .models import Sponsor

SAFE_IMAGES = {"image/png": {".png"}, "image/jpeg": {".jpg", ".jpeg"}, "image/webp": {".webp"}, "image/gif": {".gif"}}

def ready(db):
    if not inspect(db.get_bind()).has_table("sponsors"):
        raise HTTPException(503, "Sponsors database migration has not been applied")

def get(db: Session, sponsor_id: int, lock=False):
    ready(db)
    query = select(Sponsor).where(Sponsor.id == sponsor_id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if not row:
        raise HTTPException(404, "Sponsor not found")
    return row

def listing(db: Session, *, limit, offset, search=None, publish_status=None, is_active=None, public=False):
    ready(db)
    query = select(Sponsor)
    if public:
        query = query.where(Sponsor.is_active.is_(True), Sponsor.publish_status == "published")
    else:
        if search:
            query = query.where(Sponsor.name.contains(search, autoescape=True))
        if publish_status:
            query = query.where(Sponsor.publish_status == publish_status)
        if is_active is not None:
            query = query.where(Sponsor.is_active == is_active)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return db.scalars(query.order_by(Sponsor.display_order, Sponsor.id).limit(limit).offset(offset)).unique().all(), total

def validate(db: Session, fields):
    media_id = fields.get("logo_media_id")
    if media_id:
        media = db.get(MediaFile, media_id)
        if not media or media.mime_type not in SAFE_IMAGES or Path(media.stored_filename).suffix.lower() not in SAFE_IMAGES.get(media.mime_type, set()):
            raise HTTPException(422, "Choose an existing PNG, JPEG, WebP or GIF image from Media Library")
        # Public logo URLs come exclusively from the existing upload service.
        if not urlsplit(media.url).path.startswith("/uploads/"):
            raise HTTPException(422, "Logo must reference an uploaded media image")
    if fields.get("publish_status") == "published" and not media_id:
        raise HTTPException(422, "Select a logo before publishing")

def serialize(row):
    return {key: getattr(row, key) for key in ["id", "name", "logo_media_id", "website_url", "description", "display_order", "is_active", "publish_status", "created_at", "updated_at"]} | {"logo_url": row.logo.url if row.logo else None}

def create(db, payload):
    ready(db)
    fields = payload.model_dump()
    validate(db, fields)
    row = Sponsor(**fields)
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)

def update(db, sponsor_id, payload):
    row = get(db, sponsor_id, lock=True)
    fields = payload.model_dump(exclude_unset=True)
    expected = fields.pop("expected_updated_at", None)
    if expected is not None and expected != row.updated_at:
        raise HTTPException(409, "Sponsor was changed elsewhere. Reload before saving")
    if any(fields.get(key, getattr(row, key)) is None for key in ["name", "display_order", "is_active", "publish_status"]):
        raise HTTPException(422, "Required sponsor fields cannot be null")
    merged = {key: fields.get(key, getattr(row, key)) for key in ["logo_media_id", "publish_status"]}
    validate(db, merged)
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return serialize(row)

def delete(db, sponsor_id):
    row = get(db, sponsor_id, lock=True)
    db.delete(row)
    db.commit()
