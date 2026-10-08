from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CastingApplication(Base):
    __tablename__ = "casting_applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    stage_name: Mapped[str | None] = mapped_column(String(180), nullable=True)

    acting_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    languages: Mapped[str | None] = mapped_column(String(255), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    short_bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    headshot_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    showreel_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    previous_projects: Mapped[str | None] = mapped_column(Text, nullable=True)
    social_media: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    preferred_role: Mapped[str | None] = mapped_column(String(180), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(180), nullable=True)
    consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted", index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class FilmSubmission(Base):
    __tablename__ = "film_submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    applicant_name: Mapped[str] = mapped_column(String(180), nullable=False)
    production_company: Mapped[str | None] = mapped_column(String(180), nullable=True)
    film_title: Mapped[str] = mapped_column(String(255), nullable=False)
    film_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(80), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    year_produced: Mapped[int | None] = mapped_column(Integer, nullable=True)
    running_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    director: Mapped[str | None] = mapped_column(String(180), nullable=True)
    producer: Mapped[str | None] = mapped_column(String(180), nullable=True)
    cast_members: Mapped[str | None] = mapped_column(Text, nullable=True)

    trailer_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    film_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subtitles: Mapped[str | None] = mapped_column(String(120), nullable=True)

    previous_screenings: Mapped[str | None] = mapped_column(Text, nullable=True)
    awards: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_declaration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    contact_email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted", index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class VolunteerApplication(Base):
    __tablename__ = "volunteer_applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(180), nullable=True)
    profession: Mapped[str | None] = mapped_column(String(180), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_of_interest: Mapped[str | None] = mapped_column(String(180), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(180), nullable=True)
    previous_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    motivation: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted", index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CareerApplication(Base):
    __tablename__ = "career_applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    position_applied: Mapped[str | None] = mapped_column(String(180), nullable=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(180), nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted", index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )