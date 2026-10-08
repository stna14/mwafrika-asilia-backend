from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    original_filename: str
    stored_filename: str
    url: str
    mime_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    uploaded_by_admin_id: int | None = None
    created_at: datetime


class MediaListResponse(BaseModel):
    items: list[MediaFileOut]
    total: int
    limit: int
    offset: int