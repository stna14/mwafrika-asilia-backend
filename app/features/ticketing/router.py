from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.ticketing import service
from app.features.ticketing.checkout import authorized_order, issue_checkout_token
from app.features.ticketing.schemas import (
    CheckInRequest, CheckInResponse, CreateOrderRequest, CreateOrderResponse,
    CreatePaymentRequest, EventAdminOut, EventCreate, EventUpdate,
    GetPaymentResponse, OrderOut, PaymentOut, TierAdminOut, TierCreate,
    TierUpdate, TicketOut,
)

public_router = APIRouter(prefix="/api/tickets", tags=["ticketing"])
admin_router = APIRouter(prefix="/api/admin/tickets", tags=["ticketing (admin)"])


@public_router.get("/events")
def public_events(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    items, total = service.list_events(db, published_only=True, limit=limit, offset=offset)
    return {"success": True, "items": [service.event_to_out(e) for e in items], "total": total}


@public_router.get("/events/{event_id}")
def public_event(event_id: int, db: Session = Depends(get_db)):
    event = service.get_event(db, event_id)
    if event.publish_status != "published":
        raise HTTPException(404, "Event not found")
    tiers = service.list_tiers_for_event(db, event.id, active_only=True)
    return {"success": True, "event": service.event_to_out(event), "tiers": [service.tier_to_out(t) for t in tiers]}


@public_router.post("/orders", response_model=CreateOrderResponse)
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db),
                 idempotency_key: str = Header(alias="Idempotency-Key")):
    try:
        order = service.create_order(db, payload, idempotency_key)
        return CreateOrderResponse(success=True, order=OrderOut(**service.order_to_out(db, order)),
                                   checkoutToken=issue_checkout_token(order))
    except Exception:
        db.rollback()
        raise


@public_router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    order = authorized_order(db, order_id, authorization)
    order = service.transition_order(db, order)
    return OrderOut(**service.order_to_out(db, order))


@public_router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: str, db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    order = authorized_order(db, order_id, authorization)
    # Admin/finance read access is not cancellation authority. Only the scoped
    # checkout capability (returned to the buyer) can cancel through this route.
    from app.core.security import decode_access_token
    token = decode_access_token(authorization.split(" ", 1)[1])
    if not token or token.get("scope") != "ticket_checkout":
        raise HTTPException(403, "Buyer checkout authorization is required to cancel")
    try:
        order = service.transition_order(db, order, cancel=True)
        return OrderOut(**service.order_to_out(db, order))
    except Exception:
        db.rollback()
        raise


@public_router.get("/orders/{order_id}/tickets")
def get_order_tickets(order_id: str, db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    order = service.transition_order(db, authorized_order(db, order_id, authorization))
    tickets = service.list_tickets_for_order(db, order.id) if order.status == "PAID" else []
    return {"success": True, "tickets": [TicketOut(**service.ticket_to_out(t)) for t in tickets]}


@public_router.get("/payment-methods")
def payment_methods():
    return {"available": False, "items": [], "message": "No payment provider is verified for collection"}


@public_router.post("/payments")
def create_payment(payload: CreatePaymentRequest):
    raise HTTPException(409, "Live payment collection is not configured; no payment was initiated")


@public_router.get("/payments/{payment_id}", response_model=GetPaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db), authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(401, "Checkout authorization required")
    txn = service.get_payment(db, payment_id)
    authorized_order(db, str(txn.order_id), authorization)
    return GetPaymentResponse(success=True, transaction=PaymentOut(**service.payment_to_out(txn)))


@public_router.post("/check-in", response_model=CheckInResponse)
def check_in(payload: CheckInRequest, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    result = service.check_in_ticket(db, payload.ticketToken)
    return CheckInResponse(success=result["success"],
        ticket=TicketOut(**service.ticket_to_out(result["ticket"])) if result["ticket"] else None,
        message=result["message"])


# ---------- Admin: Events ----------

@admin_router.get("/events")
def admin_list_events(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_events(db, published_only=False, limit=limit, offset=offset)
    return {"success": True, "items": [service.event_to_out(e, admin=True) for e in items], "total": total}


@admin_router.post("/events", response_model=EventAdminOut, status_code=201)
def admin_create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    event = service.create_event(db, payload)
    return EventAdminOut(**service.event_to_out(event, admin=True))


@admin_router.get("/events/{event_id}")
def admin_get_event(
    event_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    event = service.get_event(db, event_id)
    tiers = service.list_tiers_for_event(db, event.id, active_only=False)
    return {
        "success": True,
        "event": service.event_to_out(event, admin=True),
        "tiers": [service.tier_to_out(t, admin=True) for t in tiers],
    }


@admin_router.patch("/events/{event_id}", response_model=EventAdminOut)
def admin_update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    event = service.update_event(db, event_id, payload)
    return EventAdminOut(**service.event_to_out(event, admin=True))


@admin_router.delete("/events/{event_id}", status_code=204)
def admin_delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_event(db, event_id)


# ---------- Admin: Tiers ----------

@admin_router.post("/tiers", response_model=TierAdminOut, status_code=201)
def admin_create_tier(
    payload: TierCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    tier = service.create_tier(db, payload)
    return TierAdminOut(**service.tier_to_out(tier, admin=True))


@admin_router.patch("/tiers/{tier_id}", response_model=TierAdminOut)
def admin_update_tier(
    tier_id: int,
    payload: TierUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    tier = service.update_tier(db, tier_id, payload)
    return TierAdminOut(**service.tier_to_out(tier, admin=True))


@admin_router.delete("/tiers/{tier_id}", status_code=204)
def admin_delete_tier(
    tier_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_tier(db, tier_id)