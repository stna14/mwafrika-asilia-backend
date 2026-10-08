from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.wisac import service
from app.features.wisac.schemas import (
    CategoryCreate,
    CategoryGroupCreate,
    CategoryGroupListResponse,
    CategoryGroupOut,
    CategoryGroupUpdate,
    CategoryListResponse,
    CategoryOut,
    CategoryUpdate,
    ConfirmWinnerRequest,
    EditionCreate,
    EditionListResponse,
    EditionOut,
    EditionUpdate,
    NomineeCreate,
    NomineeListResponse,
    NomineeOut,
    NomineeUpdate,
    RankingsResponse,
    WinnerDetailListResponse,
    WinnerDetailOut,
)

public_router = APIRouter(prefix="/api/wisac", tags=["wisac"])
admin_router = APIRouter(prefix="/api/admin/wisac", tags=["wisac (admin)"])


# ---------- Public ----------

@public_router.get("/editions", response_model=EditionListResponse)
def public_editions(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_editions(db, limit=limit, offset=offset)
    return EditionListResponse(
        items=[EditionOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@public_router.get("/editions/{year}", response_model=EditionOut)
def public_edition_by_year(year: int, db: Session = Depends(get_db)):
    return service.get_edition_by_year(db, year)


# ---------- Admin ----------

@admin_router.get("/editions", response_model=EditionListResponse)
def admin_list_editions(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_editions(
        db, limit=limit, offset=offset, status_filter=status_filter
    )
    return EditionListResponse(
        items=[EditionOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("/editions", response_model=EditionOut, status_code=201)
def admin_create_edition(
    payload: EditionCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_edition(db, payload)


@admin_router.get("/editions/{edition_id}", response_model=EditionOut)
def admin_get_edition(
    edition_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_edition(db, edition_id)


@admin_router.patch("/editions/{edition_id}", response_model=EditionOut)
def admin_update_edition(
    edition_id: int,
    payload: EditionUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_edition(db, edition_id, payload)


@admin_router.delete("/editions/{edition_id}", status_code=204)
def admin_delete_edition(
    edition_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_edition(db, edition_id)


# ---------- Category Groups (admin only) ----------

@admin_router.get("/category-groups", response_model=CategoryGroupListResponse)
def admin_list_groups(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    edition_id: int | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_category_groups(
        db, edition_id=edition_id, limit=limit, offset=offset
    )
    return CategoryGroupListResponse(
        items=[CategoryGroupOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("/category-groups", response_model=CategoryGroupOut, status_code=201)
def admin_create_group(
    payload: CategoryGroupCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_category_group(db, payload)


@admin_router.get("/category-groups/{group_id}", response_model=CategoryGroupOut)
def admin_get_group(
    group_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_category_group(db, group_id)


@admin_router.patch("/category-groups/{group_id}", response_model=CategoryGroupOut)
def admin_update_group(
    group_id: int,
    payload: CategoryGroupUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_category_group(db, group_id, payload)


@admin_router.delete("/category-groups/{group_id}", status_code=204)
def admin_delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_category_group(db, group_id)


# ---------- Categories ----------

@public_router.get("/editions/{year}/categories", response_model=CategoryListResponse)
def public_categories_by_year(
    year: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    edition = service.get_edition_by_year(db, year)
    items, total = service.list_categories(
        db, edition_id=edition.id, limit=limit, offset=offset
    )
    return CategoryListResponse(
        items=[CategoryOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/categories", response_model=CategoryListResponse)
def admin_list_categories(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    edition_id: int | None = None,
    group_id: int | None = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_categories(
        db,
        edition_id=edition_id,
        group_id=group_id,
        limit=limit,
        offset=offset,
    )
    return CategoryListResponse(
        items=[CategoryOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("/categories", response_model=CategoryOut, status_code=201)
def admin_create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_category(db, payload)


@admin_router.get("/categories/{category_id}", response_model=CategoryOut)
def admin_get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_category(db, category_id)


@admin_router.patch("/categories/{category_id}", response_model=CategoryOut)
def admin_update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_category(db, category_id, payload)


@admin_router.delete("/categories/{category_id}", status_code=204)
def admin_delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_category(db, category_id)


# ---------- Nominees ----------

@public_router.get(
    "/editions/{year}/categories/{category_id}/nominees",
    response_model=NomineeListResponse,
)
def public_nominees_for_category(
    year: int,
    category_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    edition = service.get_edition_by_year(db, year)
    category = service.get_category(db, category_id)
    if category.edition_id != edition.id:
        raise HTTPException(
            status_code=404,
            detail="Category does not belong to this edition",
        )
    items, total = service.list_nominees(
        db,
        category_id=category_id,
        status_filter="active",
        limit=limit,
        offset=offset,
    )
    return NomineeListResponse(
        items=[NomineeOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@public_router.get("/winners", response_model=NomineeListResponse)
def public_all_winners(
    db: Session = Depends(get_db),
    edition_id: int | None = None,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_nominees(
        db,
        edition_id=edition_id,
        winner_only=True,
        limit=limit,
        offset=offset,
    )
    return NomineeListResponse(
        items=[NomineeOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/nominees", response_model=NomineeListResponse)
def admin_list_nominees(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    category_id: int | None = None,
    edition_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    winner_only: bool = False,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_nominees(
        db,
        category_id=category_id,
        edition_id=edition_id,
        status_filter=status_filter,
        winner_only=winner_only,
        limit=limit,
        offset=offset,
    )
    return NomineeListResponse(
        items=[NomineeOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("/nominees", response_model=NomineeOut, status_code=201)
def admin_create_nominee(
    payload: NomineeCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.create_nominee(db, payload)


@admin_router.get("/nominees/{nominee_id}", response_model=NomineeOut)
def admin_get_nominee(
    nominee_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_nominee(db, nominee_id)


@admin_router.patch("/nominees/{nominee_id}", response_model=NomineeOut)
def admin_update_nominee(
    nominee_id: int,
    payload: NomineeUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.update_nominee(db, nominee_id, payload)


@admin_router.delete("/nominees/{nominee_id}", status_code=204)
def admin_delete_nominee(
    nominee_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_nominee(db, nominee_id)


# ---------- Winners / Rankings ----------

@public_router.get("/winners-detailed", response_model=WinnerDetailListResponse)
def public_winners_detailed(
    db: Session = Depends(get_db),
    edition_id: int | None = None,
):
    items = service.list_winners_detailed(db, edition_id=edition_id)
    return WinnerDetailListResponse(
        items=[WinnerDetailOut(**item) for item in items],
        total=len(items),
    )


@public_router.get(
    "/editions/{year}/rankings",
    response_model=RankingsResponse,
)
def public_rankings(year: int, db: Session = Depends(get_db)):
    edition = service.get_edition_by_year(db, year)
    categories = service.list_rankings(db, edition_id=edition.id)
    return RankingsResponse(categories=categories)


@admin_router.post(
    "/categories/{category_id}/confirm-winner",
    response_model=NomineeOut,
)
def admin_confirm_winner(
    category_id: int,
    payload: ConfirmWinnerRequest,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.confirm_winner(
        db,
        category_id=category_id,
        nominee_id=payload.nominee_id,
    )
