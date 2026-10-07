from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.features.admin_auth.models import AdminUser


def get_admin_by_email(db: Session, email: str) -> AdminUser | None:
    return db.query(AdminUser).filter(AdminUser.email == email.lower()).first()


def get_admin_by_id(db: Session, admin_id: int) -> AdminUser | None:
    return db.query(AdminUser).filter(AdminUser.id == admin_id).first()


def create_admin(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    phone: str | None = None,
    role: str = "super_admin",
) -> AdminUser:
    email = email.lower().strip()
    if get_admin_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin with this email already exists",
        )
    admin = AdminUser(
        full_name=full_name.strip(),
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def authenticate_admin(db: Session, email: str, password: str) -> AdminUser:
    admin = get_admin_by_email(db, email)
    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    admin.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(admin)
    return admin