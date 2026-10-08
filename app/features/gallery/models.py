from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GalleryItem(Base):
    __tablename__ = "gallery_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(300), nullable=True)
    collection: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    publish_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="published", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )