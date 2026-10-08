from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.features.ticketing import service
from app.features.ticketing.schemas import (
    CheckInRequest,
    CheckInResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    CreatePaymentRequest,
    CreatePaymentResponse,
    EventCreate,
    EventOut,
    EventUpdate,
    GetPaymentResponse,
    OrderOut,
    PaymentOut,
    TierCreate,
    TierOut,
    TierUpdate,
    TicketOut,
)

public_router = APIRouter(prefix="/api/tickets", tags=["ticketing"])
admin_router = APIRouter(prefix="/api/admin/tickets", tags=["ticketing (admin)"])


# ---------- Public: Events ----------

@public_router.get("/events")
def public_events(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_events(db, published_only=True, limit=limit, offset=offset)
    return {
        "success": True,
        "items": [service.event_to_out(e) for e in items],
        "total": total,
    }


@public_router.get("/events/{event_id}")
def public_event(event_id: int, db: Session = Depends(get_db)):
    event = service.get_event(db, event_id)
    tiers = service.list_tiers_for_event(db, event.id, active_only=True)
    return {
        "success": True,
        "event": service.event_to_out(event),
        "tiers": [service.tier_to_out(t) for t in tiers],
    }


# ---------- Public: Orders ----------

@public_router.post("/orders", response_model=CreateOrderResponse)
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    try:
        order = service.create_order(db, payload)
    except Exception as e:
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            return CreateOrderResponse(success=False, message=str(e.detail), code="ORDER_FAILED")
        raise
    return CreateOrderResponse(success=True, order=OrderOut(**service.order_to_out(db, order)))


@public_router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = service.get_order(db, order_id)
    return OrderOut(**service.order_to_out(db, order))


@public_router.get("/orders/{order_id}/tickets")
def get_order_tickets(order_id: int, db: Session = Depends(get_db)):
    tickets = service.list_tickets_for_order(db, order_id)
    return {"success": True, "tickets": [TicketOut(**service.ticket_to_out(t)) for t in tickets]}


# ---------- Public: Payments ----------

@public_router.post("/payments", response_model=CreatePaymentResponse)
def create_payment(payload: CreatePaymentRequest, db: Session = Depends(get_db)):
    try:
        txn = service.create_payment(db, int(payload.orderId), payload.provider)
    except Exception as e:
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            return CreatePaymentResponse(success=False, message=str(e.detail), code="PAYMENT_FAILED")
        raise
    return CreatePaymentResponse(
        success=True,
        transaction=PaymentOut(**service.payment_to_out(txn)),
    )


@public_router.get("/payments/{payment_id}", response_model=GetPaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    txn = service.get_payment(db, payment_id)
    return GetPaymentResponse(success=True, transaction=PaymentOut(**service.payment_to_out(txn)))


# ---------- Public: Check-in ----------

@public_router.post("/check-in", response_model=CheckInResponse)
def check_in(payload: CheckInRequest, db: Session = Depends(get_db)):
    result = service.check_in_ticket(db, payload.ticketToken)
    return CheckInResponse(
        success=result["success"],
        ticket=TicketOut(**service.ticket_to_out(result["ticket"])) if result["ticket"] else None,
        message=result["message"],
    )


# ---------- Admin: Events ----------

@admin_router.get("/events")
def admin_list_events(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = service.list_events(db, published_only=False, limit=limit, offset=offset)
    return {"success": True, "items": [service.event_to_out(e) for e in items], "total": total}


@admin_router.post("/events", response_model=EventOut, status_code=201)
def admin_create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    event = service.create_event(db, payload)
    return EventOut(**service.event_to_out(event))


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
        "event": service.event_to_out(event),
        "tiers": [service.tier_to_out(t) for t in tiers],
    }


@admin_router.patch("/events/{event_id}", response_model=EventOut)
def admin_update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    event = service.update_event(db, event_id, payload)
    return EventOut(**service.event_to_out(event))


@admin_router.delete("/events/{event_id}", status_code=204)
def admin_delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_event(db, event_id)


# ---------- Admin: Tiers ----------

@admin_router.post("/tiers", response_model=TierOut, status_code=201)
def admin_create_tier(
    payload: TierCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    tier = service.create_tier(db, payload)
    return TierOut(**service.tier_to_out(tier))


@admin_router.patch("/tiers/{tier_id}", response_model=TierOut)
def admin_update_tier(
    tier_id: int,
    payload: TierUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    tier = service.update_tier(db, tier_id, payload)
    return TierOut(**service.tier_to_out(tier))


@admin_router.delete("/tiers/{tier_id}", status_code=204)
def admin_delete_tier(
    tier_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_tier(db, tier_id)