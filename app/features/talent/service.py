import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, inspect
from sqlalchemy.orm import Session

from app.features.talent.models import (
    CareerApplication,
    CastingApplication,
    FilmSubmission,
    VolunteerApplication,
    PartnershipApplication,
)
from app.features.talent.schemas import (
    ApplicationUpdate,
    CareerCreate,
    CastingCreate,
    FilmCreate,
    VolunteerCreate,
)

MODEL_MAP = {
    "casting": CastingApplication,
    "film": FilmSubmission,
    "volunteer": VolunteerApplication,
    "career": CareerApplication,
    "partner": PartnershipApplication,
}


def _model(db: Session, kind: str):
    model = MODEL_MAP.get(kind)
    if kind == "partner" and not inspect(db.get_bind()).has_table("partnership_applications"):
        raise HTTPException(status_code=503, detail="Partnership database migration has not been applied")
    return model


def _new_public_id() -> str:
    return str(uuid.uuid4())


def create_application(db: Session, kind: str, payload) -> Any:
    model = _model(db, kind)
    if model is None:
        raise HTTPException(status_code=400, detail="Unknown application type")

    data = payload.model_dump()
    data["public_id"] = _new_public_id()

    obj = model(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_application(db: Session, kind: str, application_id: int):
    model = _model(db, kind)
    if model is None:
        raise HTTPException(status_code=400, detail="Unknown application type")

    obj = db.query(model).filter(model.id == application_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return obj


def get_application_by_public_id(db: Session, kind: str, public_id: str):
    model = _model(db, kind)
    if model is None:
        return None
    return db.query(model).filter(model.public_id == public_id).first()


def list_applications(
    db: Session,
    kind: str,
    *,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list, int]:
    model = _model(db, kind)
    if model is None:
        raise HTTPException(status_code=400, detail="Unknown application type")

    query = db.query(model)
    if status_filter:
        query = query.filter(model.status == status_filter)

    if search:
        like = f"%{search.strip()}%"
        # All four models have `full_name` OR (film: applicant_name) and email
        if kind == "partner":
            query = query.filter(model.contact_name.ilike(like) | model.email.ilike(like) | model.organization.ilike(like))
        elif hasattr(model, "full_name"):
            query = query.filter(model.full_name.ilike(like) | model.email.ilike(like))
        else:
            query = query.filter(
                model.applicant_name.ilike(like) | model.contact_email.ilike(like)
            )

    total = query.with_entities(func.count(model.id)).scalar() or 0
    items = (
        query.order_by(model.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_application(
    db: Session, kind: str, application_id: int, payload: ApplicationUpdate
):
    obj = get_application(db, kind, application_id)
    data = payload.model_dump(exclude_unset=True)
    if kind == "partner":
        if "status" in data and data["status"] is None:
            raise HTTPException(status_code=422, detail="Status cannot be null")
        if data.get("admin_notes") and len(data["admin_notes"]) > 10000:
            raise HTTPException(status_code=422, detail="Review notes must not exceed 10000 characters")
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_application(db: Session, kind: str, application_id: int) -> None:
    obj = get_application(db, kind, application_id)
    db.delete(obj)
    db.commit()