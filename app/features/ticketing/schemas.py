from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal[
    "PENDING_PAYMENT",
    "PAYMENT_PROCESSING",
    "PAID",
    "FAILED",
    "CANCELLED",
    "EXPIRED",
    "REFUNDED",
]

PaymentStatus = Literal[
    "CREATED",
    "PENDING",
    "PROCESSING",
    "SUCCESS",
    "FAILED",
    "CANCELLED",
    "EXPIRED",
]

TicketStatus = Literal["VALID", "USED", "CANCELLED", "EXPIRED"]


# ---------- Event ----------

class EventBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=5)
    cover_image_url: str = Field(min_length=1, max_length=500)
    event_datetime: datetime
    venue: str = Field(min_length=2, max_length=255)
    price_label: str | None = Field(default=None, max_length=50)
    publish_status: Literal["draft", "published", "archived"] = "draft"
    display_order: int = Field(default=0, ge=0)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, min_length=5)
    cover_image_url: str | None = Field(default=None, min_length=1, max_length=500)
    event_datetime: datetime | None = None
    venue: str | None = Field(default=None, min_length=2, max_length=255)
    price_label: str | None = Field(default=None, max_length=50)
    publish_status: Literal["draft", "published", "archived"] | None = None
    display_order: int | None = Field(default=None, ge=0)


class EventOut(BaseModel):
    id: str
    title: str
    date: str
    time: str
    venue: str
    description: str
    image: str
    category: str
    priceLabel: str


# ---------- Ticket Tier ----------

class TierBase(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    short_name: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1)
    benefits: list[str] = Field(default_factory=list)
    price: float = Field(ge=0)
    currency: str = Field(default="TZS", max_length=10)
    quantity_total: int = Field(ge=0)
    max_per_order: int = Field(default=10, ge=1)
    status: Literal["active", "inactive"] = "active"
    display_order: int = Field(default=0, ge=0)


class TierCreate(TierBase):
    event_id: int


class TierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    short_name: str | None = Field(default=None, min_length=1, max_length=40)
    description: str | None = Field(default=None, min_length=1)
    benefits: list[str] | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    quantity_total: int | None = Field(default=None, ge=0)
    max_per_order: int | None = Field(default=None, ge=1)
    status: Literal["active", "inactive"] | None = None
    display_order: int | None = Field(default=None, ge=0)


class TierOut(BaseModel):
    id: str
    eventId: str
    name: str
    shortName: str
    price: float
    currency: str
    description: str
    benefits: list[str]
    maxQuantity: int
    available: int


# ---------- Orders ----------

class OrderItemRequest(BaseModel):
    ticketTypeId: str
    quantity: int = Field(ge=1)


class CreateOrderRequest(BaseModel):
    eventId: str
    items: list[OrderItemRequest]
    buyerName: str | None = None
    buyerEmail: str | None = None
    buyerPhone: str | None = None


class OrderItemOut(BaseModel):
    id: str
    orderId: str
    ticketTypeId: str
    ticketName: str
    quantity: int
    unitPrice: float
    subtotal: float


class OrderOut(BaseModel):
    id: str
    publicId: str
    eventId: str
    eventTitle: str
    status: OrderStatus
    items: list[OrderItemOut]
    subtotal: float
    fees: float
    discount: float
    total: float
    currency: str
    buyerReference: str | None = None
    createdAt: datetime
    updatedAt: datetime
    expiresAt: datetime | None = None
    paidAt: datetime | None = None


class CreateOrderResponse(BaseModel):
    success: bool
    order: OrderOut | None = None
    message: str | None = None
    code: str | None = None


# ---------- Payments ----------

class CreatePaymentRequest(BaseModel):
    orderId: str
    provider: str = "mock"


class PaymentOut(BaseModel):
    id: str
    publicId: str
    orderId: str
    provider: str
    providerReference: str | None = None
    amount: float
    currency: str
    status: PaymentStatus
    createdAt: datetime
    updatedAt: datetime
    paidAt: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class CreatePaymentResponse(BaseModel):
    success: bool
    transaction: PaymentOut | None = None
    message: str | None = None
    code: str | None = None


class GetPaymentResponse(BaseModel):
    success: bool
    transaction: PaymentOut | None = None


# ---------- Tickets ----------

class TicketOut(BaseModel):
    id: str
    publicId: str
    orderId: str
    eventId: str
    ticketTypeId: str
    ticketToken: str
    ticketName: str
    status: TicketStatus
    attendeeName: str | None = None
    issuedAt: datetime | None = None
    usedAt: datetime | None = None
    createdAt: datetime


class CheckInRequest(BaseModel):
    ticketToken: str


class CheckInResponse(BaseModel):
    success: bool
    ticket: TicketOut | None = None
    message: str