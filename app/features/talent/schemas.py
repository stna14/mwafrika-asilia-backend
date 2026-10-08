from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ApplicationStatus = Literal["submitted", "under_review", "shortlisted", "approved", "rejected"]


# ---------- Casting ----------

class CastingCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    nationality: str | None = Field(default=None, max_length=80)
    region: str | None = Field(default=None, max_length=120)
    phone: str = Field(min_length=5, max_length=32)
    email: EmailStr
    stage_name: str | None = Field(default=None, max_length=180)
    acting_experience: str | None = None
    skills: str | None = None
    languages: str | None = Field(default=None, max_length=255)
    height_cm: int | None = Field(default=None, ge=50, le=250)
    short_bio: str | None = None
    profile_photo_url: str | None = Field(default=None, max_length=500)
    headshot_url: str | None = Field(default=None, max_length=500)
    full_photo_url: str | None = Field(default=None, max_length=500)
    showreel_url: str | None = Field(default=None, max_length=500)
    previous_projects: str | None = None
    social_media: dict = Field(default_factory=dict)
    preferred_role: str | None = Field(default=None, max_length=180)
    availability: str | None = Field(default=None, max_length=180)
    consent: bool = False


class CastingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    full_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    nationality: str | None = None
    region: str | None = None
    phone: str
    email: EmailStr
    stage_name: str | None = None
    acting_experience: str | None = None
    skills: str | None = None
    languages: str | None = None
    height_cm: int | None = None
    short_bio: str | None = None
    profile_photo_url: str | None = None
    headshot_url: str | None = None
    full_photo_url: str | None = None
    showreel_url: str | None = None
    previous_projects: str | None = None
    social_media: dict = Field(default_factory=dict)
    preferred_role: str | None = None
    availability: str | None = None
    consent: bool
    status: ApplicationStatus
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _id_str(cls, v): return str(v)

    @field_validator("social_media", mode="before")
    @classmethod
    def _sm(cls, v): return v or {}


# ---------- Film ----------

class FilmCreate(BaseModel):
    applicant_name: str = Field(min_length=2, max_length=180)
    production_company: str | None = Field(default=None, max_length=180)
    film_title: str = Field(min_length=1, max_length=255)
    film_type: str | None = Field(default=None, max_length=80)
    genre: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, max_length=80)
    year_produced: int | None = Field(default=None, ge=1900, le=2100)
    running_time_minutes: int | None = Field(default=None, ge=1, le=1000)
    language: str | None = Field(default=None, max_length=80)
    synopsis: str | None = None
    director: str | None = Field(default=None, max_length=180)
    producer: str | None = Field(default=None, max_length=180)
    cast_members: str | None = None
    trailer_url: str | None = Field(default=None, max_length=500)
    film_url: str | None = Field(default=None, max_length=500)
    poster_url: str | None = Field(default=None, max_length=500)
    subtitles: str | None = Field(default=None, max_length=120)
    previous_screenings: str | None = None
    awards: str | None = None
    rights_declaration: bool = False
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=32)


class FilmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    applicant_name: str
    production_company: str | None = None
    film_title: str
    film_type: str | None = None
    genre: str | None = None
    country: str | None = None
    year_produced: int | None = None
    running_time_minutes: int | None = None
    language: str | None = None
    synopsis: str | None = None
    director: str | None = None
    producer: str | None = None
    cast_members: str | None = None
    trailer_url: str | None = None
    film_url: str | None = None
    poster_url: str | None = None
    subtitles: str | None = None
    previous_screenings: str | None = None
    awards: str | None = None
    rights_declaration: bool
    contact_email: EmailStr
    contact_phone: str | None = None
    status: ApplicationStatus
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _id_str(cls, v): return str(v)


# ---------- Volunteer ----------

class VolunteerCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    age: int | None = Field(default=None, ge=13, le=100)
    phone: str = Field(min_length=5, max_length=32)
    email: EmailStr
    location: str | None = Field(default=None, max_length=180)
    profession: str | None = Field(default=None, max_length=180)
    skills: str | None = None
    area_of_interest: str | None = Field(default=None, max_length=180)
    availability: str | None = Field(default=None, max_length=180)
    previous_experience: str | None = None
    cv_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)
    motivation: str | None = None


class VolunteerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    full_name: str
    age: int | None = None
    phone: str
    email: EmailStr
    location: str | None = None
    profession: str | None = None
    skills: str | None = None
    area_of_interest: str | None = None
    availability: str | None = None
    previous_experience: str | None = None
    cv_url: str | None = None
    portfolio_url: str | None = None
    motivation: str | None = None
    status: ApplicationStatus
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _id_str(cls, v): return str(v)


# ---------- Career ----------

class CareerCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=32)
    position_applied: str | None = Field(default=None, max_length=180)
    cover_letter: str | None = None
    resume_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)
    availability: str | None = Field(default=None, max_length=180)


class CareerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    full_name: str
    email: EmailStr
    phone: str
    position_applied: str | None = None
    cover_letter: str | None = None
    resume_url: str | None = None
    portfolio_url: str | None = None
    availability: str | None = None
    status: ApplicationStatus
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _id_str(cls, v): return str(v)


# ---------- Shared: admin update & submit responses ----------

class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    admin_notes: str | None = None


class ApplicationSubmitResponse(BaseModel):
    success: bool
    public_id: str | None = None
    message: str