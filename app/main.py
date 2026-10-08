from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.audit_middleware import AdminAuditMiddleware
from app.core.config import settings
from app.core.database import engine, init_db
from app.features.admin_auth.router import router as admin_auth_router
from app.features.audit_logs.router import router as audit_logs_router
from app.features.cms.router import (
    admin_router as cms_admin_router,
    pages_admin_router as cms_pages_admin_router,
    pages_public_router as cms_pages_public_router,
    projects_admin_router as cms_projects_admin_router,
    projects_public_router as cms_projects_public_router,
    public_router as cms_public_router,
    settings_admin_router as cms_settings_admin_router,
    settings_public_router as cms_settings_public_router,
)
from app.features.gallery.router import (
    admin_router as gallery_admin_router,
    public_router as gallery_public_router,
)
from app.features.media_library.router import router as media_router
from app.features.newsroom.router import (
    admin_router as newsroom_admin_router,
    public_router as newsroom_public_router,
)
from app.features.talent.router import (
    admin_router as talent_admin_router,
    public_router as talent_public_router,
)
from app.features.ticketing.router import (
    admin_router as ticketing_admin_router,
    public_router as ticketing_public_router,
)
from app.features.voting.router import router as voting_router
from app.features.wisac.router import (
    admin_router as wisac_admin_router,
    public_router as wisac_public_router,
)


settings.upload_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(AdminAuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_path)),
    name="uploads",
)

app.include_router(admin_auth_router)
app.include_router(audit_logs_router)
app.include_router(cms_admin_router)
app.include_router(cms_public_router)
app.include_router(cms_pages_admin_router)
app.include_router(cms_pages_public_router)
app.include_router(cms_projects_admin_router)
app.include_router(cms_projects_public_router)
app.include_router(cms_settings_public_router)
app.include_router(cms_settings_admin_router)
app.include_router(newsroom_public_router)
app.include_router(newsroom_admin_router)
app.include_router(wisac_public_router)
app.include_router(wisac_admin_router)
app.include_router(voting_router)
app.include_router(gallery_public_router)
app.include_router(gallery_admin_router)
app.include_router(ticketing_public_router)
app.include_router(ticketing_admin_router)
app.include_router(talent_public_router)
app.include_router(talent_admin_router)
app.include_router(media_router)


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT DATABASE(), VERSION();")).fetchone()
        return {"status": "ok", "database": row[0], "mysql_version": row[1]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}