from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PublishStatus = Literal["draft", "published", "archived"]


class GalleryItemBase(BaseModel):
    image_url: str = Field(min_length=1, max_length=500)
    caption: str | None = Field(default=None, max_length=300)
    collection: str | None = Field(default=None, max_length=80)
    display_order: int = Field(default=0, ge=0)
    publish_status: PublishStatus = "published"

    @field_validator("caption", "collection", mode="before")
    @classmethod
    def _strip_optional(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class GalleryItemCreate(GalleryItemBase):
    pass


class GalleryItemUpdate(BaseModel):
    image_url: str | None = Field(default=None, min_length=1, max_length=500)
    caption: str | None = Field(default=None, max_length=300)
    collection: str | None = Field(default=None, max_length=80)
    display_order: int | None = Field(default=None, ge=0)
    publish_status: PublishStatus | None = None

    @field_validator("caption", "collection", mode="before")
    @classmethod
    def _strip_optional(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class GalleryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    caption: str | None = None
    collection: str | None = None
    display_order: int
    publish_status: PublishStatus
    created_at: datetime
    updated_at: datetime


class GalleryListResponse(BaseModel):
    items: list[GalleryItemOut]
    total: int
    limit: int
    offset: int