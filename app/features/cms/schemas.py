from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ServiceStatus = Literal["draft", "published", "archived"]


# ---------- Services ----------

class ServiceBase(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    short_description: str = Field(min_length=5, max_length=300)
    full_description: str = Field(min_length=10)
    cover_image_url: str | None = Field(default=None, max_length=500)
    icon_url: str | None = Field(default=None, max_length=500)
    cta_text: str | None = Field(default=None, max_length=80)
    cta_link: str | None = Field(default=None, max_length=255)
    status: ServiceStatus = "draft"
    display_order: int = Field(default=0, ge=0)


class ServiceCreate(ServiceBase):
    slug: str | None = Field(default=None, max_length=180)

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=180)
    short_description: str | None = Field(default=None, min_length=5, max_length=300)
    full_description: str | None = Field(default=None, min_length=10)
    cover_image_url: str | None = Field(default=None, max_length=500)
    icon_url: str | None = Field(default=None, max_length=500)
    cta_text: str | None = Field(default=None, max_length=80)
    cta_link: str | None = Field(default=None, max_length=255)
    status: ServiceStatus | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    short_description: str
    full_description: str
    cover_image_url: str | None = None
    icon_url: str | None = None
    cta_text: str | None = None
    cta_link: str | None = None
    status: ServiceStatus
    display_order: int
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(BaseModel):
    items: list[ServiceOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------- Pages ----------

class PageBase(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    content: str = Field(min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=500)
    seo_title: str | None = Field(default=None, max_length=180)
    seo_description: str | None = Field(default=None, max_length=300)
    status: ServiceStatus = "draft"


class PageCreate(PageBase):
    slug: str | None = Field(default=None, max_length=120)

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class PageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=120)
    content: str | None = Field(default=None, min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=500)
    seo_title: str | None = Field(default=None, max_length=180)
    seo_description: str | None = Field(default=None, max_length=300)
    status: ServiceStatus | None = None

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    content: str
    cover_image_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    status: ServiceStatus
    created_at: datetime
    updated_at: datetime


class PageListResponse(BaseModel):
    items: list[PageOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------- Projects ----------

class ProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    short_description: str = Field(min_length=5, max_length=300)
    cover_image_url: str = Field(min_length=1, max_length=500)
    publish_status: ServiceStatus = "draft"
    display_order: int = Field(default=0, ge=0)


class ProjectCreate(ProjectBase):
    slug: str | None = Field(default=None, max_length=180)

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=180)
    short_description: str | None = Field(default=None, min_length=5, max_length=300)
    cover_image_url: str | None = Field(default=None, min_length=1, max_length=500)
    publish_status: ServiceStatus | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("slug", mode="before")
    @classmethod
    def _clean_slug(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    short_description: str
    cover_image_url: str
    publish_status: ServiceStatus
    display_order: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------- Website Settings ----------

class WebsiteSettingUpdate(BaseModel):
    instagram_url: str | None = Field(default=None, max_length=500)
    facebook_url: str | None = Field(default=None, max_length=500)
    twitter_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    whatsapp_url: str | None = Field(default=None, max_length=500)
    tagline: str | None = Field(default=None, max_length=500)


class WebsiteSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_url: str | None = None
    facebook_url: str | None = None
    twitter_url: str | None = None
    linkedin_url: str | None = None
    whatsapp_url: str | None = None
    tagline: str | None = None
    updated_at: datetime