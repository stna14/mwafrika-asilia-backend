import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.features.ticketing.checkout import idempotent_order_id, assert_replay_matches

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

def event_to_out(event: Event, *, admin: bool = False) -> dict:
    result = {
        "id": str(event.id),
        "title": event.title,
        "date": _format_event_date(event.event_datetime),
        "time": _format_event_time(event.event_datetime),
        "event_datetime": event.event_datetime.isoformat(),
        "venue": event.venue,
        "description": event.description,
        "image": event.cover_image_url,
        "category": event.category,
        "priceLabel": event.price_label or "",
    }

    if admin:
        result.update(publish_status=event.publish_status, display_order=event.display_order)
    return result


def tier_to_out(tier: TicketType, *, admin: bool = False) -> dict:
    available = max(
        0, (tier.quantity_total or 0) - (tier.quantity_reserved or 0) - (tier.quantity_sold or 0)
    )
    result = {
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

    if admin:
        result.update(quantity_total=tier.quantity_total, quantity_reserved=tier.quantity_reserved,
                      quantity_sold=tier.quantity_sold, max_per_order=tier.max_per_order,
                      status=tier.status, display_order=tier.display_order)
    return result


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
        if v is None and k not in {"price_label"}:
            raise HTTPException(422, "Event fields cannot be cleared")
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
    tier = db.query(TicketType).filter(TicketType.id == tier_id).with_for_update().first()
    if tier is None:
        raise HTTPException(404, "Ticket type not found")
    total = payload.quantity_total
    if total is not None and total < tier.quantity_reserved + tier.quantity_sold:
        raise HTTPException(409, "Total inventory cannot be lower than reserved plus sold tickets")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if v is None:
            raise HTTPException(422, "Ticket category fields cannot be cleared")
        setattr(tier, k, v)
    db.commit()
    db.refresh(tier)
    return tier


def delete_tier(db: Session, tier_id: int) -> None:
    tier = get_tier(db, tier_id)
    db.delete(tier)
    db.commit()


# ---------- Orders ----------

def release_order_inventory(db: Session, order: Order, terminal_status: str) -> None:
    # Caller holds the event and order locks. Only active reservations release stock.
    if order.status not in {"PENDING_PAYMENT", "PAYMENT_PROCESSING"}:
        return
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).order_by(OrderItem.ticket_type_id).all()
    for item in items:
        tier = db.query(TicketType).filter(TicketType.id == item.ticket_type_id).with_for_update().first()
        if tier is None or tier.quantity_reserved < item.quantity:
            raise HTTPException(409, "Reservation inventory needs administrator review")
        tier.quantity_reserved -= item.quantity
    order.status = terminal_status
    order.updated_at = datetime.utcnow()


def expire_event_orders(db: Session, event_id: int, now: datetime) -> None:
    expired = db.query(Order).filter(Order.event_id == event_id,
        Order.status.in_(["PENDING_PAYMENT", "PAYMENT_PROCESSING"]),
        Order.expires_at < now).order_by(Order.id).with_for_update().all()
    for order in expired:
        release_order_inventory(db, order, "EXPIRED")


def create_order(db: Session, payload, idempotency_key: str) -> Order:
    public_id = idempotent_order_id(idempotency_key)
    # One event lock serializes stock reservations and expiry releases for that event.
    event = db.query(Event).filter(Event.id == int(payload.eventId)).with_for_update().first()
    if event is None:
        raise HTTPException(404, "Event not found")
    replay = db.query(Order).filter(Order.public_id == public_id).with_for_update().first()
    if replay:
        assert_replay_matches(db, replay, payload)
        db.commit()
        return replay
    if event.publish_status != "published":
        raise HTTPException(409, "Event is not available for purchase")
    now = datetime.utcnow()
    expire_event_orders(db, event.id, now)
    chosen = []
    currency = None
    subtotal = Decimal("0.00")
    for item_req in sorted(payload.items, key=lambda item: int(item.ticketTypeId)):
        tier = db.query(TicketType).filter(TicketType.id == int(item_req.ticketTypeId)).with_for_update().first()
        if tier is None or tier.event_id != event.id:
            raise HTTPException(400, "Ticket category does not belong to this event")
        if tier.status != "active":
            raise HTTPException(409, "Ticket category is not available")
        available = tier.quantity_total - tier.quantity_reserved - tier.quantity_sold
        if item_req.quantity > tier.max_per_order:
            raise HTTPException(400, f"Maximum {tier.max_per_order} tickets per order")
        if item_req.quantity > available:
            raise HTTPException(409, f"Only {max(0, available)} tickets remain")
        if currency is not None and currency != tier.currency:
            raise HTTPException(400, "An order cannot mix currencies")
        currency = tier.currency
        line = Decimal(str(tier.price)) * item_req.quantity
        subtotal += line
        chosen.append((tier, item_req.quantity, line))
    order = Order(public_id=public_id, event_id=event.id, status="PENDING_PAYMENT",
        subtotal=subtotal, fees=0, discount=0, total=subtotal, currency=currency or "TZS",
        buyer_name=payload.buyerName, buyer_email=str(payload.buyerEmail), buyer_phone=payload.buyerPhone,
        buyer_reference=payload.buyerPhone, created_at=now, updated_at=now,
        expires_at=now + timedelta(minutes=ORDER_EXPIRY_MINUTES))
    try:
        db.add(order)
        db.flush()
        for tier, quantity, line in chosen:
            db.add(OrderItem(public_id=_new_public_id(), order_id=order.id,
                ticket_type_id=tier.id, ticket_name=tier.name, quantity=quantity,
                unit_price=tier.price, subtotal=line))
            tier.quantity_reserved += quantity
        db.commit()
    except IntegrityError:
        db.rollback()
        replay = db.query(Order).filter(Order.public_id == public_id).first()
        if replay:
            assert_replay_matches(db, replay, payload)
            return replay
        raise HTTPException(409, "Order reservation conflicted; retry with the same idempotency key")
    db.refresh(order)
    return order


def transition_order(db: Session, order: Order, *, cancel: bool = False) -> Order:
    db.query(Event).filter(Event.id == order.event_id).with_for_update().first()
    order = db.query(Order).filter(Order.id == order.id).with_for_update().populate_existing().first()
    if cancel:
        if order.status not in {"PENDING_PAYMENT", "PAYMENT_PROCESSING", "CANCELLED", "EXPIRED"}:
            raise HTTPException(409, "This order cannot be cancelled")
        release_order_inventory(db, order, "CANCELLED")
    elif order.expires_at and order.expires_at < datetime.utcnow():
        release_order_inventory(db, order, "EXPIRED")
    db.commit()
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
    # Fail before touching orders/transactions. No provider has been verified.
    raise HTTPException(409, "Live payment collection is not configured; no payment was initiated")


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
    return db.query(Ticket).filter(Ticket.ticket_token == token).with_for_update().first()


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