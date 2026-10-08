from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.gallery import service
from app.features.gallery.schemas import (
    GalleryItemCreate,
    GalleryItemOut,
    GalleryItemUpdate,
    GalleryListResponse,
)

public_router = APIRouter(prefix="/api/gallery", tags=["gallery"])
admin_router = APIRouter(prefix="/api/admin/gallery", tags=["gallery (admin)"])


# ---------- Public ----------

@public_router.get("", response_model=GalleryListResponse)
def public_list(
    db: Session = Depends(get_db),
    collection: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_items(
        db,
        collection=collection,
        published_only=True,
        limit=limit,
        offset=offset,
    )
    return GalleryListResponse(
        items=[GalleryItemOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@public_router.get("/{item_id}", response_model=GalleryItemOut)
def public_get(item_id: int, db: Session = Depends(get_db)):
    item = service.get_item(db, item_id)
    if item.publish_status != "published":
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Gallery item not found")
    return item


# ---------- Admin ----------

@admin_router.get("", response_model=GalleryListResponse)
def admin_list(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    collection: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_items(
        db,
        collection=collection,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return GalleryListResponse(
        items=[GalleryItemOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("", response_model=GalleryItemOut, status_code=201)
def admin_create(
    payload: GalleryItemCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_item(db, payload)


@admin_router.get("/{item_id}", response_model=GalleryItemOut)
def admin_get(
    item_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_item(db, item_id)


@admin_router.patch("/{item_id}", response_model=GalleryItemOut)
def admin_update(
    item_id: int,
    payload: GalleryItemUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_item(db, item_id, payload)


@admin_router.delete("/{item_id}", status_code=204)
def admin_delete(
    item_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_item(db, item_id)