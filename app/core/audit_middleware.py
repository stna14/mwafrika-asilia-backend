import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.features.audit_logs.models import AdminAuditLog

ACTION_MAP = {
    "POST": "create",
    "PATCH": "update",
    "PUT": "update",
    "DELETE": "delete",
}


def _parse_entity(path: str) -> tuple[str, str | None]:
    stripped = path.replace("/api/admin/", "", 1)
    parts = stripped.split("/")
    if parts and parts[-1].isdigit():
        return "/".join(parts[:-1]), parts[-1]
    return stripped, None


def _safe_body(raw: bytes) -> dict | list | None:
    if not raw:
        return None
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        return None
    if len(text) > 5000:
        text = text[:5000] + "...[truncated]"
    try:
        return json.loads(text)
    except Exception:
        return {"_raw": text}


class AdminAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        should_log = (
            path.startswith("/api/admin/")
            and method in ACTION_MAP
            and path != "/api/admin/login"
        )

        body_bytes: bytes = b""
        if should_log:
            try:
                body_bytes = await request.body()

                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}

                request._receive = receive
            except Exception:
                body_bytes = b""

        response = await call_next(request)

        if should_log:
            admin_id: int | None = None
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
                payload = decode_access_token(token)
                if payload and payload.get("sub"):
                    try:
                        admin_id = int(payload["sub"])
                    except Exception:
                        admin_id = None

            entity_type, entity_id = _parse_entity(path)

            db = SessionLocal()
            try:
                log = AdminAuditLog(
                    admin_id=admin_id,
                    action=ACTION_MAP[method],
                    entity_type=entity_type,
                    entity_id=entity_id,
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    request_body=_safe_body(body_bytes),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                db.add(log)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

        return response