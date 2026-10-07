from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(180), unique=True, nullable=False, index=True
    )
    short_description: Mapped[str] = mapped_column(String(300), nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)

    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    cta_text: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cta_link: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    slug: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    seo_title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    slug: Mapped[str] = mapped_column(
        String(180), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    short_description: Mapped[str] = mapped_column(String(300), nullable=False)
    cover_image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    publish_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WebsiteSetting(Base):
    __tablename__ = "website_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    whatsapp_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tagline: Mapped[str | None] = mapped_column(String(500), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )