"""Scoped checkout capabilities and durable idempotency using existing columns.

The existing unique orders.public_id index is the idempotency boundary. No
schema mutation or in-memory cache is required. Keep request keys private.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt

from app.core.config import settings
from app.core.security import decode_access_token
from app.features.ticketing.models import Order, OrderItem


def idempotent_order_id(key: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", key):
        raise HTTPException(422, "Supply a private random Idempotency-Key (16–128 characters)")
    digest = hashlib.sha256(("order:" + key).encode()).hexdigest()
    return "MW-" + digest[:48].upper()


def issue_checkout_token(order: Order) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": order.public_id, "scope": "ticket_checkout",
                       "iat": now, "exp": now + timedelta(days=90)},
                      settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def assert_replay_matches(db, order: Order, payload) -> None:
    stored = {"eventId": str(order.event_id), "buyerName": order.buyer_name,
              "buyerEmail": order.buyer_email, "buyerPhone": order.buyer_phone,
              "items": sorted((str(i.ticket_type_id), i.quantity) for i in
                              db.query(OrderItem).filter(OrderItem.order_id == order.id).all())}
    requested = {"eventId": payload.eventId, "buyerName": payload.buyerName,
                 "buyerEmail": str(payload.buyerEmail), "buyerPhone": payload.buyerPhone,
                 "items": sorted((i.ticketTypeId, i.quantity) for i in payload.items)}
    if json.dumps(stored, sort_keys=True) != json.dumps(requested, sort_keys=True):
        raise HTTPException(409, "Idempotency key was already used with different order details")


def authorized_order(db, order_id: str, authorization: str | None) -> Order:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Checkout authorization required")
    payload = decode_access_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(401, "Invalid or expired checkout authorization")
    privileged = False
    if payload.get("scope") != "ticket_checkout":
        from app.features.admin_auth.models import AdminUser
        subject = str(payload.get("sub", ""))
        if payload.get("scope") is None and subject.isdigit():
            admin = db.query(AdminUser).filter(AdminUser.id == int(subject)).first()
            privileged = bool(admin and admin.is_active and admin.role in {"admin", "super_admin", "finance"})
        if not privileged:
            raise HTTPException(403, "This token cannot access checkout data")
    query = db.query(Order)
    order = query.filter(Order.id == int(order_id)).first() if order_id.isdigit() else query.filter(Order.public_id == order_id).first()
    if order is None or (not privileged and not hmac.compare_digest(str(payload.get("sub", "")), order.public_id)):
        raise HTTPException(404, "Order not found")
    return order
