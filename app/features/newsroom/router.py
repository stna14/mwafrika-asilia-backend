from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.newsroom import service
from app.features.newsroom.schemas import (
    NewsDetailResponse,
    NewsListResponse,
    NewsPostCreate,
    NewsPostOut,
    NewsPostSummaryOut,
    NewsPostUpdate,
)

public_router = APIRouter(prefix="/api/news", tags=["newsroom"])
admin_router = APIRouter(prefix="/api/admin/news", tags=["newsroom (admin)"])


# ---------- Public ----------

@public_router.get("", response_model=NewsListResponse)
def public_list(
    db: Session = Depends(get_db),
    type_filter: str | None = Query(None, alias="type"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_posts(
        db,
        limit=limit,
        offset=offset,
        type_filter=type_filter,
        published_only=True,
    )
    return NewsListResponse(
        items=[NewsPostSummaryOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@public_router.get("/{slug}", response_model=NewsDetailResponse)
def public_get(slug: str, db: Session = Depends(get_db)):
    try:
        post = service.get_post_by_slug(db, slug, published_only=True)
    except Exception:
        return NewsDetailResponse(success=False, item=None, message="Not found")
    return NewsDetailResponse(
        success=True, item=NewsPostOut.model_validate(post)
    )


# ---------- Admin ----------

@admin_router.get("", response_model=NewsListResponse)
def admin_list(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    type_filter: str | None = Query(None, alias="type"),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_posts(
        db,
        limit=limit,
        offset=offset,
        type_filter=type_filter,
        status_filter=status_filter,
        search=search,
    )
    return NewsListResponse(
        items=[NewsPostSummaryOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("", response_model=NewsPostOut, status_code=201)
def admin_create(
    payload: NewsPostCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_post(db, payload)


@admin_router.get("/{post_id}", response_model=NewsPostOut)
def admin_get(
    post_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_post(db, post_id)


@admin_router.patch("/{post_id}", response_model=NewsPostOut)
def admin_update(
    post_id: int,
    payload: NewsPostUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_post(db, post_id, payload)


@admin_router.delete("/{post_id}", status_code=204)
def admin_delete(
    post_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_post(db, post_id)