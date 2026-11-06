from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.features.media_library.models import MediaFile

class Sponsor(Base):
    __tablename__ = "sponsors"
    __table_args__ = (
        CheckConstraint("publish_status IN ('draft','published')", name="ck_sponsors_publication"),
        CheckConstraint("display_order >= 0", name="ck_sponsors_order"),
        Index("ix_sponsors_public_order", "is_active", "publish_status", "display_order", "id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    logo_media_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("media_files.id", ondelete="RESTRICT"), nullable=True)
    logo: Mapped[MediaFile | None] = relationship(lazy="joined")
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    publish_status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
