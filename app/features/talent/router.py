from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.talent import service
from app.features.talent.schemas import (
    ApplicationSubmitResponse,
    ApplicationUpdate,
    CareerCreate,
    CareerOut,
    CastingCreate,
    CastingOut,
    FilmCreate,
    FilmOut,
    VolunteerCreate,
    VolunteerOut,
)

public_router = APIRouter(prefix="/api/talent", tags=["talent"])
admin_router = APIRouter(prefix="/api/admin/talent", tags=["talent (admin)"])

OUT_MAP = {
    "casting": CastingOut,
    "film": FilmOut,
    "volunteer": VolunteerOut,
    "career": CareerOut,
}


def _response_for(kind: str, obj):
    return OUT_MAP[kind].model_validate(obj)


# ---------- Public ----------

@public_router.post("/casting", response_model=ApplicationSubmitResponse, status_code=201)
def submit_casting(payload: CastingCreate, db: Session = Depends(get_db)):
    obj = service.create_application(db, "casting", payload)
    return ApplicationSubmitResponse(success=True, public_id=obj.public_id, message="Application received.")


@public_router.post("/film", response_model=ApplicationSubmitResponse, status_code=201)
def submit_film(payload: FilmCreate, db: Session = Depends(get_db)):
    obj = service.create_application(db, "film", payload)
    return ApplicationSubmitResponse(success=True, public_id=obj.public_id, message="Film submission received.")


@public_router.post("/volunteer", response_model=ApplicationSubmitResponse, status_code=201)
def submit_volunteer(payload: VolunteerCreate, db: Session = Depends(get_db)):
    obj = service.create_application(db, "volunteer", payload)
    return ApplicationSubmitResponse(success=True, public_id=obj.public_id, message="Volunteer application received.")


@public_router.post("/career", response_model=ApplicationSubmitResponse, status_code=201)
def submit_career(payload: CareerCreate, db: Session = Depends(get_db)):
    obj = service.create_application(db, "career", payload)
    return ApplicationSubmitResponse(success=True, public_id=obj.public_id, message="Career application received.")


@public_router.get("/status/{kind}/{public_id}")
def public_status(kind: str, public_id: str, db: Session = Depends(get_db)):
    obj = service.get_application_by_public_id(db, kind, public_id)
    if obj is None:
        return {"success": False, "message": "Not found"}
    return {
        "success": True,
        "public_id": obj.public_id,
        "status": obj.status,
        "created_at": obj.created_at,
    }


# ---------- Admin ----------

@admin_router.get("/{kind}")
def admin_list(
    kind: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if kind not in OUT_MAP:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Unknown application type")
    items, total = service.list_applications(
        db, kind, status_filter=status_filter, search=search, limit=limit, offset=offset
    )
    return {
        "success": True,
        "items": [_response_for(kind, i) for i in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@admin_router.get("/{kind}/{application_id}")
def admin_get(
    kind: str,
    application_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    obj = service.get_application(db, kind, application_id)
    return _response_for(kind, obj)


@admin_router.patch("/{kind}/{application_id}")
def admin_update(
    kind: str,
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    obj = service.update_application(db, kind, application_id, payload)
    return _response_for(kind, obj)


@admin_router.delete("/{kind}/{application_id}", status_code=204)
def admin_delete(
    kind: str,
    application_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_application(db, kind, application_id)