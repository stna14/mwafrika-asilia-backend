from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.cms import service
from app.features.cms.schemas import (
    PageCreate,
    PageListResponse,
    PageOut,
    PageUpdate,
    ProjectCreate,
    ProjectListResponse,
    ProjectOut,
    ProjectUpdate,
    ServiceCreate,
    ServiceListResponse,
    ServiceOut,
    ServiceUpdate,
    WebsiteSettingOut,
    WebsiteSettingUpdate,
)


# ---------- Services ----------
public_router = APIRouter(prefix="/api/services", tags=["services"])
admin_router = APIRouter(prefix="/api/admin/services", tags=["services (admin)"])


@public_router.get("", response_model=ServiceListResponse)
def public_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    items, total = service.list_services(
        db, page=page, page_size=page_size, published_only=True
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    return ServiceListResponse(
        items=[ServiceOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@public_router.get("/{slug}", response_model=ServiceOut)
def public_get(slug: str, db: Session = Depends(get_db)):
    return service.get_service_by_slug(db, slug, published_only=True)


@admin_router.get("", response_model=ServiceListResponse)
def admin_list(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
):
    items, total = service.list_services(
        db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    return ServiceListResponse(
        items=[ServiceOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@admin_router.post("", response_model=ServiceOut, status_code=201)
def admin_create(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_service(db, payload)


@admin_router.get("/{service_id}", response_model=ServiceOut)
def admin_get(
    service_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_service(db, service_id)


@admin_router.patch("/{service_id}", response_model=ServiceOut)
def admin_update(
    service_id: int,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_service(db, service_id, payload)


@admin_router.delete("/{service_id}", status_code=204)
def admin_delete(
    service_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_service(db, service_id)


# ---------- Pages ----------
pages_public_router = APIRouter(prefix="/api/pages", tags=["pages"])
pages_admin_router = APIRouter(prefix="/api/admin/pages", tags=["pages (admin)"])


@pages_public_router.get("", response_model=PageListResponse)
def public_pages_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    items, total = service.list_pages(
        db, page=page, page_size=page_size, published_only=True
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    return PageListResponse(
        items=[PageOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@pages_public_router.get("/{slug}", response_model=PageOut)
def public_page_get(slug: str, db: Session = Depends(get_db)):
    return service.get_page_by_slug(db, slug, published_only=True)


@pages_admin_router.get("", response_model=PageListResponse)
def admin_pages_list(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
):
    items, total = service.list_pages(
        db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    return PageListResponse(
        items=[PageOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@pages_admin_router.post("", response_model=PageOut, status_code=201)
def admin_page_create(
    payload: PageCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_page(db, payload)


@pages_admin_router.get("/{page_id}", response_model=PageOut)
def admin_page_get(
    page_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_page(db, page_id)


@pages_admin_router.patch("/{page_id}", response_model=PageOut)
def admin_page_update(
    page_id: int,
    payload: PageUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_page(db, page_id, payload)


@pages_admin_router.delete("/{page_id}", status_code=204)
def admin_page_delete(
    page_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_page(db, page_id)


# ---------- Projects ----------
projects_public_router = APIRouter(prefix="/api/projects", tags=["projects"])
projects_admin_router = APIRouter(prefix="/api/admin/projects", tags=["projects (admin)"])


@projects_public_router.get("", response_model=ProjectListResponse)
def public_projects_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    items, total = service.list_projects(
        db, page=page, page_size=page_size, published_only=True
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    return ProjectListResponse(
        items=[ProjectOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@projects_public_router.get("/{slug}", response_model=ProjectOut)
def public_project_get(slug: str, db: Session = Depends(get_db)):
    return service.get_project_by_slug(db, slug, published_only=True)


@projects_admin_router.get("", response_model=ProjectListResponse)
def admin_projects_list(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
):
    items, total = service.list_projects(
        db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if page_size else 0
    return ProjectListResponse(
        items=[ProjectOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@projects_admin_router.post("", response_model=ProjectOut, status_code=201)
def admin_project_create(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_project(db, payload)


@projects_admin_router.get("/{project_id}", response_model=ProjectOut)
def admin_project_get(
    project_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_project(db, project_id)


@projects_admin_router.patch("/{project_id}", response_model=ProjectOut)
def admin_project_update(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_project(db, project_id, payload)


@projects_admin_router.delete("/{project_id}", status_code=204)
def admin_project_delete(
    project_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_project(db, project_id)


# ---------- Website Settings ----------
settings_public_router = APIRouter(prefix="/api/settings", tags=["settings"])
settings_admin_router = APIRouter(prefix="/api/admin/settings", tags=["settings (admin)"])


@settings_public_router.get("", response_model=WebsiteSettingOut)
def public_settings(db: Session = Depends(get_db)):
    return service.get_settings(db)


@settings_admin_router.get("", response_model=WebsiteSettingOut)
def admin_settings_get(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_settings(db)


@settings_admin_router.patch("", response_model=WebsiteSettingOut)
def admin_settings_update(
    payload: WebsiteSettingUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_settings(db, payload)