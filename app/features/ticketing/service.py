import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.features.ticketing.models import (
    Event,
    Order,
    OrderItem,
    Ticket,
    TicketPayment,
    TicketType,
)

ORDER_EXPIRY_MINUTES = 30


# ---------- Helpers ----------

def _new_public_id() -> str:
    return str(uuid.uuid4())


def _new_order_public_id() -> str:
    return "MW-" + secrets.token_hex(4).upper()


def _new_ticket_token() -> str:
    return secrets.token_urlsafe(24)


def _format_event_date(dt: datetime) -> str:
    return dt.strftime("%A, %d %B %Y")


def _format_event_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


# ---------- Event serialization ----------

def event_to_out(event: Event) -> dict:
    return {
        "id": str(event.id),
        "title": event.title,
        "date": _format_event_date(event.event_datetime),
        "time": _format_event_time(event.event_datetime),
        "venue": event.venue,
        "description": event.description,
        "image": event.cover_image_url,
        "category": event.category,
        "priceLabel": event.price_label or "",
    }


def tier_to_out(tier: TicketType) -> dict:
    available = max(
        0, (tier.quantity_total or 0) - (tier.quantity_reserved or 0) - (tier.quantity_sold or 0)
    )
    return {
        "id": str(tier.id),
        "eventId": str(tier.event_id),
        "name": tier.name,
        "shortName": tier.short_name,
        "price": float(tier.price),
        "currency": tier.currency,
        "description": tier.description,
        "benefits": tier.benefits or [],
        "maxQuantity": tier.max_per_order,
        "available": available,
    }


# ---------- Event CRUD ----------

def create_event(db: Session, payload) -> Event:
    event = Event(
        public_id=_new_public_id(),
        **payload.model_dump(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def list_events(
    db: Session, *, published_only: bool = False, limit: int = 100, offset: int = 0
) -> tuple[list[Event], int]:
    query = db.query(Event)
    if published_only:
        query = query.filter(Event.publish_status == "published")
    total = query.count()
    items = (
        query.order_by(Event.display_order.asc(), Event.event_datetime.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_event(db: Session, event_id: int, payload) -> Event:
    event = get_event(db, event_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(event, k, v)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int) -> None:
    event = get_event(db, event_id)
    db.delete(event)
    db.commit()


# ---------- Tier CRUD ----------

def create_tier(db: Session, payload) -> TicketType:
    get_event(db, payload.event_id)
    data = payload.model_dump()
    tier = TicketType(public_id=_new_public_id(), **data)
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def get_tier(db: Session, tier_id: int) -> TicketType:
    tier = db.query(TicketType).filter(TicketType.id == tier_id).first()
    if tier is None:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    return tier


def list_tiers_for_event(
    db: Session, event_id: int, *, active_only: bool = False
) -> list[TicketType]:
    query = db.query(TicketType).filter(TicketType.event_id == event_id)
    if active_only:
        query = query.filter(TicketType.status == "active")
    return query.order_by(TicketType.display_order.asc(), TicketType.id.asc()).all()


def update_tier(db: Session, tier_id: int, payload) -> TicketType:
    tier = get_tier(db, tier_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(tier, k, v)
    db.commit()
    db.refresh(tier)
    return tier


def delete_tier(db: Session, tier_id: int) -> None:
    tier = get_tier(db, tier_id)
    db.delete(tier)
    db.commit()


# ---------- Orders ----------

def create_order(db: Session, payload) -> Order:
    event = get_event(db, int(payload.eventId))
    if event.publish_status != "published":
        raise HTTPException(status_code=409, detail="Event is not available for purchase")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    now = datetime.utcnow()
    order = Order(
        public_id=_new_order_public_id(),
        event_id=event.id,
        status="PENDING_PAYMENT",
        subtotal=0,
        fees=0,
        discount=0,
        total=0,
        currency="TZS",
        buyer_name=payload.buyerName,
        buyer_email=payload.buyerEmail,
        buyer_phone=payload.buyerPhone,
        buyer_reference=payload.buyerPhone or payload.buyerEmail,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(minutes=ORDER_EXPIRY_MINUTES),
    )
    db.add(order)
    db.flush()

    subtotal = 0.0
    for item_req in payload.items:
        tier = get_tier(db, int(item_req.ticketTypeId))
        if tier.event_id != event.id:
            raise HTTPException(status_code=400, detail="Ticket type does not belong to this event")
        if tier.status != "active":
            raise HTTPException(status_code=409, detail=f"{tier.name} is not available")

        available = (tier.quantity_total or 0) - (tier.quantity_reserved or 0) - (tier.quantity_sold or 0)
        if item_req.quantity > tier.max_per_order:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {tier.max_per_order} tickets per order for {tier.name}",
            )
        if item_req.quantity > available:
            raise HTTPException(
                status_code=409,
                detail=f"Only {available} tickets left for {tier.name}",
            )

        line_subtotal = float(tier.price) * item_req.quantity
        subtotal += line_subtotal

        item = OrderItem(
            public_id=_new_public_id(),
            order_id=order.id,
            ticket_type_id=tier.id,
            ticket_name=tier.short_name,
            quantity=item_req.quantity,
            unit_price=float(tier.price),
            subtotal=line_subtotal,
        )
        db.add(item)

        tier.quantity_reserved = (tier.quantity_reserved or 0) + item_req.quantity

    order.subtotal = subtotal
    order.total = subtotal  # fees/discount default 0
    order.updated_at = now

    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def order_to_out(db: Session, order: Order) -> dict:
    event = db.query(Event).filter(Event.id == order.event_id).first()
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return {
        "id": str(order.id),
        "publicId": order.public_id,
        "eventId": str(order.event_id),
        "eventTitle": event.title if event else "",
        "status": order.status,
        "items": [
            {
                "id": str(i.id),
                "orderId": str(i.order_id),
                "ticketTypeId": str(i.ticket_type_id),
                "ticketName": i.ticket_name,
                "quantity": i.quantity,
                "unitPrice": float(i.unit_price),
                "subtotal": float(i.subtotal),
            }
            for i in items
        ],
        "subtotal": float(order.subtotal),
        "fees": float(order.fees),
        "discount": float(order.discount),
        "total": float(order.total),
        "currency": order.currency,
        "buyerReference": order.buyer_reference,
        "createdAt": order.created_at,
        "updatedAt": order.updated_at,
        "expiresAt": order.expires_at,
        "paidAt": order.paid_at,
    }


# ---------- Payment ----------

def create_payment(db: Session, order_id: int, provider: str) -> TicketPayment:
    order = get_order(db, order_id)
    if order.status not in ("PENDING_PAYMENT", "PAYMENT_PROCESSING"):
        raise HTTPException(status_code=409, detail=f"Order is {order.status}")

    if order.expires_at and order.expires_at < datetime.utcnow():
        order.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=409, detail="Order has expired")

    txn = TicketPayment(
        public_id=_new_public_id(),
        order_id=order.id,
        provider=provider,
        amount=float(order.total),
        currency=order.currency,
        status="CREATED",
        metadata_json={},
    )
    db.add(txn)
    order.status = "PAYMENT_PROCESSING"
    db.commit()
    db.refresh(txn)

    # Mock provider: auto-succeed immediately
    if provider == "mock":
        _mark_payment_success(db, txn)

    return txn


def get_payment(db: Session, payment_id: int) -> TicketPayment:
    txn = db.query(TicketPayment).filter(TicketPayment.id == payment_id).first()
    if txn is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return txn


def _mark_payment_success(db: Session, txn: TicketPayment) -> None:
    txn.status = "SUCCESS"
    txn.paid_at = datetime.utcnow()

    order = db.query(Order).filter(Order.id == txn.order_id).first()
    if order is None:
        db.commit()
        return

    order.status = "PAID"
    order.paid_at = datetime.utcnow()

    # Convert reserved → sold and issue tickets
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        tier = db.query(TicketType).filter(TicketType.id == item.ticket_type_id).first()
        if tier is not None:
            tier.quantity_reserved = max(0, (tier.quantity_reserved or 0) - item.quantity)
            tier.quantity_sold = (tier.quantity_sold or 0) + item.quantity

        for _ in range(item.quantity):
            ticket = Ticket(
                public_id=_new_public_id(),
                order_id=order.id,
                event_id=order.event_id,
                ticket_type_id=item.ticket_type_id,
                ticket_token=_new_ticket_token(),
                ticket_name=item.ticket_name,
                status="VALID",
                issued_at=datetime.utcnow(),
            )
            db.add(ticket)

    db.commit()


# ---------- Tickets ----------

def list_tickets_for_order(db: Session, order_id: int) -> list[Ticket]:
    get_order(db, order_id)  # ensure order exists
    return db.query(Ticket).filter(Ticket.order_id == order_id).order_by(Ticket.id.asc()).all()


def get_ticket_by_token(db: Session, token: str) -> Ticket | None:
    return db.query(Ticket).filter(Ticket.ticket_token == token).first()


def check_in_ticket(db: Session, token: str) -> dict:
    ticket = get_ticket_by_token(db, token)
    if ticket is None:
        return {"success": False, "ticket": None, "message": "Invalid ticket token"}
    if ticket.status == "USED":
        return {"success": False, "ticket": ticket, "message": "Ticket already used"}
    if ticket.status != "VALID":
        return {"success": False, "ticket": ticket, "message": f"Ticket is {ticket.status}"}

    ticket.status = "USED"
    ticket.used_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return {"success": True, "ticket": ticket, "message": "Checked in successfully"}


def ticket_to_out(ticket: Ticket) -> dict:
    return {
        "id": str(ticket.id),
        "publicId": ticket.public_id,
        "orderId": str(ticket.order_id),
        "eventId": str(ticket.event_id),
        "ticketTypeId": str(ticket.ticket_type_id),
        "ticketToken": ticket.ticket_token,
        "ticketName": ticket.ticket_name,
        "status": ticket.status,
        "attendeeName": ticket.attendee_name,
        "issuedAt": ticket.issued_at,
        "usedAt": ticket.used_at,
        "createdAt": ticket.created_at,
    }


def payment_to_out(txn: TicketPayment) -> dict:
    return {
        "id": str(txn.id),
        "publicId": txn.public_id,
        "orderId": str(txn.order_id),
        "provider": txn.provider,
        "providerReference": txn.provider_reference,
        "amount": float(txn.amount),
        "currency": txn.currency,
        "status": txn.status,
        "createdAt": txn.created_at,
        "updatedAt": txn.updated_at,
        "paidAt": txn.paid_at,
        "metadata": txn.metadata_json or {},
    }