import re
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.newsroom.models import NewsPost
from app.features.newsroom.schemas import NewsPostCreate, NewsPostUpdate


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def _unique_slug(db: Session, base_slug: str, exclude_id: int | None = None) -> str:
    slug = base_slug or "post"
    counter = 2
    while True:
        query = db.query(NewsPost).filter(NewsPost.slug == slug)
        if exclude_id is not None:
            query = query.filter(NewsPost.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create_post(db: Session, payload: NewsPostCreate) -> NewsPost:
    base_slug = payload.slug or _slugify(payload.title)
    slug = _unique_slug(db, base_slug)

    published_at = payload.published_at
    if payload.status == "published" and published_at is None:
        published_at = datetime.utcnow()

    post = NewsPost(
        slug=slug,
        title=payload.title.strip(),
        type=payload.type,
        status=payload.status,
        excerpt=payload.excerpt.strip(),
        body=payload.body,
        author=payload.author.strip(),
        featured_image=payload.featured_image,
        tags=payload.tags or [],
        published_at=published_at,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post(db: Session, post_id: int) -> NewsPost:
    post = db.query(NewsPost).filter(NewsPost.id == post_id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


def get_post_by_slug(db: Session, slug: str, published_only: bool = False) -> NewsPost:
    query = db.query(NewsPost).filter(NewsPost.slug == slug)
    if published_only:
        query = query.filter(NewsPost.status == "published")
    post = query.first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


def list_posts(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
    type_filter: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    published_only: bool = False,
) -> tuple[list[NewsPost], int]:
    query = db.query(NewsPost)

    if published_only:
        query = query.filter(NewsPost.status == "published")
    elif status_filter:
        query = query.filter(NewsPost.status == status_filter)

    if type_filter:
        query = query.filter(NewsPost.type == type_filter)

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (NewsPost.title.ilike(like)) | (NewsPost.excerpt.ilike(like))
        )

    total = query.with_entities(func.count(NewsPost.id)).scalar() or 0

    items = (
        query.order_by(
            NewsPost.published_at.desc(),
            NewsPost.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_post(db: Session, post_id: int, payload: NewsPostUpdate) -> NewsPost:
    post = get_post(db, post_id)
    data = payload.model_dump(exclude_unset=True)

    if "title" in data and data["title"]:
        data["title"] = data["title"].strip()
        if not data.get("slug"):
            data["slug"] = _slugify(data["title"])

    if "slug" in data and data["slug"]:
        data["slug"] = _unique_slug(db, data["slug"], exclude_id=post.id)

    if "excerpt" in data and data["excerpt"]:
        data["excerpt"] = data["excerpt"].strip()

    if "author" in data and data["author"]:
        data["author"] = data["author"].strip()

    # Auto-set published_at when status flips to published and no date given
    if data.get("status") == "published" and not data.get("published_at"):
        if post.published_at is None:
            data["published_at"] = datetime.utcnow()

    for key, value in data.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: int) -> None:
    post = get_post(db, post_id)
    db.delete(post)
    db.commit()