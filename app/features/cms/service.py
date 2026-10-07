import re

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.cms.models import Page, Project, Service, WebsiteSetting
from app.features.cms.schemas import (
    PageCreate,
    PageUpdate,
    ProjectCreate,
    ProjectUpdate,
    ServiceCreate,
    ServiceUpdate,
    WebsiteSettingUpdate,
)


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


# ---------- Services ----------

def _unique_service_slug(db: Session, base_slug: str, exclude_id: int | None = None) -> str:
    slug = base_slug or "service"
    counter = 2
    while True:
        query = db.query(Service).filter(Service.slug == slug)
        if exclude_id is not None:
            query = query.filter(Service.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create_service(db: Session, payload: ServiceCreate) -> Service:
    base_slug = payload.slug or _slugify(payload.name)
    slug = _unique_service_slug(db, base_slug)

    service = Service(
        name=payload.name.strip(),
        slug=slug,
        short_description=payload.short_description.strip(),
        full_description=payload.full_description.strip(),
        cover_image_url=payload.cover_image_url,
        icon_url=payload.icon_url,
        cta_text=payload.cta_text,
        cta_link=payload.cta_link,
        status=payload.status,
        display_order=payload.display_order,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def get_service(db: Session, service_id: int) -> Service:
    service = db.query(Service).filter(Service.id == service_id).first()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return service


def get_service_by_slug(db: Session, slug: str, published_only: bool = False) -> Service:
    query = db.query(Service).filter(Service.slug == slug)
    if published_only:
        query = query.filter(Service.status == "published")
    service = query.first()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return service


def list_services(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    search: str | None = None,
    published_only: bool = False,
) -> tuple[list[Service], int]:
    query = db.query(Service)

    if published_only:
        query = query.filter(Service.status == "published")
    elif status_filter:
        query = query.filter(Service.status == status_filter)

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (Service.name.ilike(like)) | (Service.short_description.ilike(like))
        )

    total = query.with_entities(func.count(Service.id)).scalar() or 0

    items = (
        query.order_by(Service.display_order.asc(), Service.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_service(db: Session, service_id: int, payload: ServiceUpdate) -> Service:
    service = get_service(db, service_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"]:
        data["name"] = data["name"].strip()
        if not data.get("slug"):
            data["slug"] = _slugify(data["name"])

    if "slug" in data and data["slug"]:
        data["slug"] = _unique_service_slug(db, data["slug"], exclude_id=service.id)

    if "short_description" in data and data["short_description"]:
        data["short_description"] = data["short_description"].strip()

    if "full_description" in data and data["full_description"]:
        data["full_description"] = data["full_description"].strip()

    for key, value in data.items():
        setattr(service, key, value)

    db.commit()
    db.refresh(service)
    return service


def delete_service(db: Session, service_id: int) -> None:
    service = get_service(db, service_id)
    db.delete(service)
    db.commit()


# ---------- Pages ----------

def _unique_page_slug(db: Session, base_slug: str, exclude_id: int | None = None) -> str:
    slug = base_slug or "page"
    counter = 2
    while True:
        query = db.query(Page).filter(Page.slug == slug)
        if exclude_id is not None:
            query = query.filter(Page.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create_page(db: Session, payload: PageCreate) -> Page:
    base_slug = payload.slug or _slugify(payload.title)
    slug = _unique_page_slug(db, base_slug)

    page = Page(
        slug=slug,
        title=payload.title.strip(),
        content=payload.content,
        cover_image_url=payload.cover_image_url,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        status=payload.status,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def get_page(db: Session, page_id: int) -> Page:
    page = db.query(Page).filter(Page.id == page_id).first()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


def get_page_by_slug(db: Session, slug: str, published_only: bool = False) -> Page:
    query = db.query(Page).filter(Page.slug == slug)
    if published_only:
        query = query.filter(Page.status == "published")
    page = query.first()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


def list_pages(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    search: str | None = None,
    published_only: bool = False,
) -> tuple[list[Page], int]:
    query = db.query(Page)

    if published_only:
        query = query.filter(Page.status == "published")
    elif status_filter:
        query = query.filter(Page.status == status_filter)

    if search:
        like = f"%{search.strip()}%"
        query = query.filter((Page.title.ilike(like)) | (Page.slug.ilike(like)))

    total = query.with_entities(func.count(Page.id)).scalar() or 0

    items = (
        query.order_by(Page.title.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_page(db: Session, page_id: int, payload: PageUpdate) -> Page:
    page = get_page(db, page_id)
    data = payload.model_dump(exclude_unset=True)

    if "title" in data and data["title"]:
        data["title"] = data["title"].strip()
        if not data.get("slug"):
            data["slug"] = _slugify(data["title"])

    if "slug" in data and data["slug"]:
        data["slug"] = _unique_page_slug(db, data["slug"], exclude_id=page.id)

    for key, value in data.items():
        setattr(page, key, value)

    db.commit()
    db.refresh(page)
    return page


def delete_page(db: Session, page_id: int) -> None:
    page = get_page(db, page_id)
    db.delete(page)
    db.commit()


# ---------- Projects ----------

def _unique_project_slug(db: Session, base_slug: str, exclude_id: int | None = None) -> str:
    slug = base_slug or "project"
    counter = 2
    while True:
        query = db.query(Project).filter(Project.slug == slug)
        if exclude_id is not None:
            query = query.filter(Project.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create_project(db: Session, payload: ProjectCreate) -> Project:
    base_slug = payload.slug or _slugify(payload.name)
    slug = _unique_project_slug(db, base_slug)

    project = Project(
        slug=slug,
        name=payload.name.strip(),
        short_description=payload.short_description.strip(),
        cover_image_url=payload.cover_image_url,
        publish_status=payload.publish_status,
        display_order=payload.display_order,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


def get_project_by_slug(db: Session, slug: str, published_only: bool = False) -> Project:
    query = db.query(Project).filter(Project.slug == slug)
    if published_only:
        query = query.filter(Project.publish_status == "published")
    project = query.first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


def list_projects(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    search: str | None = None,
    published_only: bool = False,
) -> tuple[list[Project], int]:
    query = db.query(Project)

    if published_only:
        query = query.filter(Project.publish_status == "published")
    elif status_filter:
        query = query.filter(Project.publish_status == status_filter)

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(
            (Project.name.ilike(like)) | (Project.short_description.ilike(like))
        )

    total = query.with_entities(func.count(Project.id)).scalar() or 0

    items = (
        query.order_by(Project.display_order.asc(), Project.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_project(db: Session, project_id: int, payload: ProjectUpdate) -> Project:
    project = get_project(db, project_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"]:
        data["name"] = data["name"].strip()
        if not data.get("slug"):
            data["slug"] = _slugify(data["name"])

    if "slug" in data and data["slug"]:
        data["slug"] = _unique_project_slug(db, data["slug"], exclude_id=project.id)

    for key, value in data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> None:
    project = get_project(db, project_id)
    db.delete(project)
    db.commit()


# ---------- Website Settings ----------

def _default_settings() -> dict:
    return {
        "instagram_url": None,
        "facebook_url": None,
        "twitter_url": None,
        "linkedin_url": None,
        "whatsapp_url": None,
        "tagline": (
            "Elevating African stories. Empowering creative excellence. "
            "Built on authentic storytelling and cultural pride."
        ),
    }


def get_settings(db: Session) -> WebsiteSetting:
    setting = db.query(WebsiteSetting).order_by(WebsiteSetting.id.asc()).first()
    if setting is None:
        setting = WebsiteSetting(**_default_settings())
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def update_settings(db: Session, payload: WebsiteSettingUpdate) -> WebsiteSetting:
    setting = get_settings(db)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(setting, key, value)
    db.commit()
    db.refresh(setting)
    return setting