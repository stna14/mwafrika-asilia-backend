from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    event_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)

    price_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    publish_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TicketType(Base):
    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    short_name: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    benefits: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="TZS")

    quantity_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    max_per_order: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("events.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING_PAYMENT", index=True
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    fees: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="TZS")

    buyer_reference: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    buyer_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    buyer_email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    buyer_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticket_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ticket_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    ticket_name: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class TicketPayment(Base):
    __tablename__ = "ticket_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="TZS")

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CREATED", index=True
    )
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("events.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ticket_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ticket_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    ticket_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    ticket_name: Mapped[str] = mapped_column(String(80), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VALID", index=True
    )
    attendee_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)