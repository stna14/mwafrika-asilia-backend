from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.audit_logs import service
from app.features.audit_logs.schemas import AuditLogListResponse, AuditLogOut

router = APIRouter(prefix="/api/admin/audit-logs", tags=["audit (admin)"])


@router.get("", response_model=AuditLogListResponse)
def list_logs(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    admin_id: int | None = None,
    entity_type: str | None = None,
    action: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_logs(
        db,
        admin_id=admin_id,
        entity_type=entity_type,
        action=action,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{log_id}", response_model=AuditLogOut)
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_log(db, log_id)