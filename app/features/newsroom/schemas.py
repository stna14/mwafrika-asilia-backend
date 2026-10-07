from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ContentType = Literal["news", "announcement", "story", "blog", "interview"]
ContentStatus = Literal["published", "draft", "archived"]


class NewsPostBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    type: ContentType
    excerpt: str = Field(min_length=5, max_length=500)
    body: str = Field(min_length=1)
    author: str = Field(min_length=2, max_length=120)
    featured_image: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list)
    status: ContentStatus = "draft"
    published_at: datetime | None = None


class NewsPostCreate(NewsPostBase):
    slug: str | None = Field(default=None, max_length=200)

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, v):
        if not isinstance(v, list):
            return []
        cleaned = [str(t).strip() for t in v if str(t).strip()]
        return list(dict.fromkeys(cleaned))


class NewsPostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=200)
    type: ContentType | None = None
    excerpt: str | None = Field(default=None, min_length=5, max_length=500)
    body: str | None = Field(default=None, min_length=1)
    author: str | None = Field(default=None, min_length=2, max_length=120)
    featured_image: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    status: ContentStatus | None = None
    published_at: datetime | None = None

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, v):
        if v is None:
            return None
        if not isinstance(v, list):
            return []
        cleaned = [str(t).strip() for t in v if str(t).strip()]
        return list(dict.fromkeys(cleaned))


class NewsPostSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    type: ContentType
    status: ContentStatus
    excerpt: str
    author: str
    featured_image: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _id_to_str(cls, v):
        return str(v)


class NewsPostOut(NewsPostSummaryOut):
    body: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def _tags_default(cls, v):
        return v or []


class NewsListResponse(BaseModel):
    items: list[NewsPostSummaryOut]
    total: int
    limit: int
    offset: int


class NewsDetailResponse(BaseModel):
    success: bool
    item: NewsPostOut | None = None
    message: str | None = None