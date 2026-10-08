from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EditionStatus = Literal["upcoming", "voting", "closed", "completed"]


# ---------- Editions ----------

class EditionBase(BaseModel):
    year: int = Field(ge=2000, le=2100)
    name: str = Field(min_length=2, max_length=180)
    theme: str | None = Field(default=None, max_length=255)
    event_date: datetime | None = None
    venue: str | None = Field(default=None, max_length=255)
    voting_start: datetime | None = None
    voting_end: datetime | None = None
    ticket_sales_start: datetime | None = None
    ticket_sales_end: datetime | None = None
    status: EditionStatus = "upcoming"
    live_stream_url: str | None = Field(default=None, max_length=500)
    description: str | None = None


class EditionCreate(EditionBase):
    pass


class EditionUpdate(BaseModel):
    year: int | None = Field(default=None, ge=2000, le=2100)
    name: str | None = Field(default=None, min_length=2, max_length=180)
    theme: str | None = Field(default=None, max_length=255)
    event_date: datetime | None = None
    venue: str | None = Field(default=None, max_length=255)
    voting_start: datetime | None = None
    voting_end: datetime | None = None
    ticket_sales_start: datetime | None = None
    ticket_sales_end: datetime | None = None
    status: EditionStatus | None = None
    live_stream_url: str | None = Field(default=None, max_length=500)
    description: str | None = None


class EditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    name: str
    theme: str | None = None
    event_date: datetime | None = None
    venue: str | None = None
    voting_start: datetime | None = None
    voting_end: datetime | None = None
    ticket_sales_start: datetime | None = None
    ticket_sales_end: datetime | None = None
    status: EditionStatus
    live_stream_url: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class EditionListResponse(BaseModel):
    items: list[EditionOut]
    total: int
    limit: int
    offset: int


# ---------- Category Groups ----------

class CategoryGroupBase(BaseModel):
    edition_id: int
    name: str = Field(min_length=2, max_length=120)
    display_order: int = Field(default=0, ge=0)


class CategoryGroupCreate(CategoryGroupBase):
    pass


class CategoryGroupUpdate(BaseModel):
    edition_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    display_order: int | None = Field(default=None, ge=0)


class CategoryGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    edition_id: int
    name: str
    display_order: int
    created_at: datetime
    updated_at: datetime


class CategoryGroupListResponse(BaseModel):
    items: list[CategoryGroupOut]
    total: int
    limit: int
    offset: int


# ---------- Categories ----------

VotingStatus = Literal["closed", "open", "paused"]


class CategoryBase(BaseModel):
    edition_id: int
    group_id: int | None = None
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    voting_status: VotingStatus = "closed"
    vote_price: float | None = Field(default=None, ge=0)
    display_order: int = Field(default=0, ge=0)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    edition_id: int | None = None
    group_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    voting_status: VotingStatus | None = None
    vote_price: float | None = Field(default=None, ge=0)
    display_order: int | None = Field(default=None, ge=0)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    edition_id: int
    group_id: int | None = None
    name: str
    description: str | None = None
    voting_status: VotingStatus
    vote_price: float | None = None
    display_order: int
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    items: list[CategoryOut]
    total: int
    limit: int
    offset: int


# ---------- Nominees ----------

NomineeStatus = Literal["active", "suspended"]


class NomineeBase(BaseModel):
    category_id: int
    full_name: str = Field(min_length=2, max_length=180)
    stage_name: str | None = Field(default=None, max_length=180)
    profile_image_url: str | None = Field(default=None, max_length=500)
    biography: str | None = None
    profession: str | None = Field(default=None, max_length=120)
    social_media: dict = Field(default_factory=dict)
    status: NomineeStatus = "active"


class NomineeCreate(NomineeBase):
    pass


class NomineeUpdate(BaseModel):
    category_id: int | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=180)
    stage_name: str | None = Field(default=None, max_length=180)
    profile_image_url: str | None = Field(default=None, max_length=500)
    biography: str | None = None
    profession: str | None = Field(default=None, max_length=120)
    social_media: dict | None = None
    status: NomineeStatus | None = None
    winner: bool | None = None


class NomineeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    edition_id: int
    full_name: str
    stage_name: str | None = None
    profile_image_url: str | None = None
    biography: str | None = None
    profession: str | None = None
    social_media: dict = Field(default_factory=dict)
    total_free_votes: int
    total_paid_votes: int
    total_votes: int
    status: NomineeStatus
    winner: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("social_media", mode="before")
    @classmethod
    def _social_default(cls, v):
        return v or {}


class NomineeListResponse(BaseModel):
    items: list[NomineeOut]
    total: int
    limit: int
    offset: int


# ---------- Winners / Rankings ----------

class WinnerDetailOut(BaseModel):
    nominee_id: int
    name: str
    image: str | None = None
    category_id: int
    category_name: str
    edition_id: int
    edition_year: int
    total_votes: int
    total_free_votes: int
    total_paid_votes: int
    winner: bool


class WinnerDetailListResponse(BaseModel):
    items: list[WinnerDetailOut]
    total: int


class CategoryRankingOut(BaseModel):
    category_id: int
    category_name: str
    edition_id: int
    edition_year: int
    nominees: list[WinnerDetailOut]


class RankingsResponse(BaseModel):
    categories: list[CategoryRankingOut]


class ConfirmWinnerRequest(BaseModel):
    nominee_id: int
