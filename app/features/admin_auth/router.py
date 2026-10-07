from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.security import create_access_token
from app.features.admin_auth import service
from app.features.admin_auth.models import AdminUser
from app.features.admin_auth.schemas import AdminLogin, AdminOut, TokenResponse

router = APIRouter(prefix="/api/admin", tags=["admin_auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: AdminLogin, db: Session = Depends(get_db)):
    admin = service.authenticate_admin(db, payload.email, payload.password)
    token = create_access_token(subject=admin.id)
    return TokenResponse(access_token=token, admin=AdminOut.model_validate(admin))


@router.get("/me", response_model=AdminOut)
def me(current: AdminUser = Depends(get_current_admin)):
    return current