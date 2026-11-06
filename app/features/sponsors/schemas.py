from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator

class SponsorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=180)
    logo_media_id: int | None = Field(default=None, gt=0, strict=True)
    website_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    display_order: int = Field(default=0, ge=0, le=2147483647, strict=True)
    is_active: bool = Field(default=True, strict=True)
    publish_status: Literal["draft", "published"] = "draft"

    @field_validator("website_url")
    @classmethod
    def safe_url(cls, value):
        if not value:
            return None
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
            raise ValueError("Use an HTTP(S) website URL without credentials")
        try:
            parts.port
        except ValueError:
            raise ValueError("Invalid website port")
        return value

class SponsorUpdate(SponsorCreate):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    display_order: int | None = Field(default=None, ge=0, le=2147483647, strict=True)
    is_active: bool | None = Field(default=None, strict=True)
    publish_status: Literal["draft", "published"] | None = None
    expected_updated_at: datetime | None = None

class SponsorPublic(BaseModel):
    id: int
    name: str
    logo_url: str | None
    website_url: str | None
    description: str | None
    display_order: int

class SponsorOut(SponsorPublic):
    logo_media_id: int | None
    is_active: bool
    publish_status: str
    created_at: datetime
    updated_at: datetime

class SponsorList(BaseModel):
    items: list[SponsorOut]
    total: int
    limit: int
    offset: int

class SponsorPublicList(BaseModel):
    items: list[SponsorPublic]
    total: int
    limit: int
    offset: int
