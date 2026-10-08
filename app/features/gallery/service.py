from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.gallery.models import GalleryItem
from app.features.gallery.schemas import GalleryItemCreate, GalleryItemUpdate


def create_item(db: Session, payload: GalleryItemCreate) -> GalleryItem:
    item = GalleryItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: int) -> GalleryItem:
    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Gallery item not found"
        )
    return item


def list_items(
    db: Session,
    *,
    collection: str | None = None,
    status_filter: str | None = None,
    published_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[GalleryItem], int]:
    query = db.query(GalleryItem)

    if published_only:
        query = query.filter(GalleryItem.publish_status == "published")
    elif status_filter:
        query = query.filter(GalleryItem.publish_status == status_filter)

    if collection:
        query = query.filter(GalleryItem.collection == collection)

    total = query.with_entities(func.count(GalleryItem.id)).scalar() or 0

    items = (
        query.order_by(
            GalleryItem.display_order.asc(),
            GalleryItem.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_item(
    db: Session, item_id: int, payload: GalleryItemUpdate
) -> GalleryItem:
    item = get_item(db, item_id)
    data = payload.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> None:
    item = get_item(db, item_id)
    db.delete(item)
    db.commit()