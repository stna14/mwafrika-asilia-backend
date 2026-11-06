from fastapi import Depends, HTTPException, Request, status
from app.core.authorization import role_allows
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("scope") is not None or not str(payload.get("sub", "")).isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    from app.features.admin_auth.models import AdminUser

    admin = db.query(AdminUser).filter(AdminUser.id == int(payload["sub"])).first()
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive",
        )
    if not role_allows(admin.role, request.url.path, request.method):
        raise HTTPException(status_code=403, detail="Your role does not permit this action")
    return admin