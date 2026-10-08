from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.audit_logs.models import AdminAuditLog


def list_logs(
    db: Session,
    *,
    admin_id: int | None = None,
    entity_type: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[AdminAuditLog], int]:
    query = db.query(AdminAuditLog)

    if admin_id is not None:
        query = query.filter(AdminAuditLog.admin_id == admin_id)
    if entity_type:
        query = query.filter(AdminAuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AdminAuditLog.action == action)

    total = query.with_entities(func.count(AdminAuditLog.id)).scalar() or 0

    items = (
        query.order_by(AdminAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def get_log(db: Session, log_id: int) -> AdminAuditLog:
    log = db.query(AdminAuditLog).filter(AdminAuditLog.id == log_id).first()
    if log is None:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log