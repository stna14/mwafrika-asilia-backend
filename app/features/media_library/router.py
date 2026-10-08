from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.media_library import service
from app.features.media_library.schemas import MediaFileOut, MediaListResponse

router = APIRouter(prefix="/api/admin/media", tags=["media (admin)"])


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.post("/upload", response_model=MediaFileOut, status_code=201)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    media = await service.save_upload(
        db,
        file=file,
        admin_id=admin.id,
        base_url=_base_url(request),
    )
    return media


@router.get("", response_model=MediaListResponse)
def list_media(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_media(db, limit=limit, offset=offset)
    return MediaListResponse(
        items=[MediaFileOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{media_id}", response_model=MediaFileOut)
def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_media(db, media_id)


@router.delete("/{media_id}", status_code=204)
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_media(db, media_id)