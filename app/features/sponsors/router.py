from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_admin
from . import service
from .schemas import SponsorCreate, SponsorUpdate, SponsorOut, SponsorList, SponsorPublicList

public_router = APIRouter(prefix="/api/sponsors", tags=["sponsors"])
admin_router = APIRouter(prefix="/api/admin/sponsors", tags=["sponsors (admin)"], dependencies=[Depends(get_current_admin)])

@public_router.get("", response_model=SponsorPublicList)
def public_list(limit: int = Query(100, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    items, total = service.listing(db, limit=limit, offset=offset, public=True)
    return {"items": [service.serialize(row) for row in items], "total": total, "limit": limit, "offset": offset}

@admin_router.get("", response_model=SponsorList)
def admin_list(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), search: str | None = Query(None, max_length=180), publish_status: Literal["draft", "published"] | None = None, is_active: bool | None = None, db: Session = Depends(get_db)):
    items, total = service.listing(db, limit=limit, offset=offset, search=search, publish_status=publish_status, is_active=is_active)
    return {"items": [service.serialize(row) for row in items], "total": total, "limit": limit, "offset": offset}

@admin_router.post("", response_model=SponsorOut, status_code=201)
def create(payload: SponsorCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)

@admin_router.get("/{sponsor_id}", response_model=SponsorOut)
def get(sponsor_id: int, db: Session = Depends(get_db)):
    return service.serialize(service.get(db, sponsor_id))

@admin_router.patch("/{sponsor_id}", response_model=SponsorOut)
def update(sponsor_id: int, payload: SponsorUpdate, db: Session = Depends(get_db)):
    return service.update(db, sponsor_id, payload)

@admin_router.delete("/{sponsor_id}", status_code=204)
def delete(sponsor_id: int, db: Session = Depends(get_db)):
    service.delete(db, sponsor_id)
