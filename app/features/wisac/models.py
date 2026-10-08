from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WisacEdition(Base):
    __tablename__ = "wisac_editions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    theme: Mapped[str | None] = mapped_column(String(255), nullable=True)

    event_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)

    voting_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    voting_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    ticket_sales_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ticket_sales_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="upcoming", index=True
    )
    live_stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WisacCategoryGroup(Base):
    __tablename__ = "wisac_category_groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    edition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wisac_editions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WisacCategory(Base):
    __tablename__ = "wisac_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    edition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wisac_editions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("wisac_category_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    voting_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="closed", index=True
    )
    vote_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WisacNominee(Base):
    __tablename__ = "wisac_nominees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wisac_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wisac_editions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    stage_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    profession: Mapped[str | None] = mapped_column(String(120), nullable=True)
    social_media: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    total_free_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_paid_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    winner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
