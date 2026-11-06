"""Approved backend source regression tests, isolated from the live MySQL DB.

Run with the backend .venv Python. No application lifespan, migration, real
credentials, SMS provider or payment provider is used by this test harness.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.features.admin_auth.models import AdminUser
from app.features.admin_auth.router import router as auth_router
from app.features.newsroom.router import admin_router as news_router
from app.features.ticketing.models import Event, Order, Ticket, TicketPayment, TicketType
from app.features.ticketing.router import admin_router, public_router


@compiles(BigInteger, "sqlite")
def sqlite_integer(_type, _compiler, **_kwargs):
    return "INTEGER"


@pytest.fixture
def system(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "isolated-backend-test-secret")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)  # In-memory test schema only; never MySQL.
    with Session(engine) as db:
        for index, role in enumerate(["super_admin", "editor", "finance", "support"], 1):
            db.add(AdminUser(id=index, full_name="QA " + role, email=f"qa{index}@example.com", role=role,
                             password_hash="not-a-real-credential", is_active=True))
        for index, state in [(1, "published"), (2, "draft")]:
            db.add(Event(id=index, public_id=f"qa-event-{index}", title="QA Event", category="QA",
                         description="QA event", cover_image_url="/qa.jpg", event_datetime=datetime(2030, 1, 1),
                         venue="QA Venue", publish_status=state, display_order=3))
        db.add(TicketType(id=1, public_id="qa-tier", event_id=1, name="QA Regular", short_name="QA",
                          description="QA only", benefits=[], price=1000, currency="TZS", quantity_total=10,
                          quantity_reserved=0, quantity_sold=0, max_per_order=2, status="active", display_order=1))
        db.commit()
    app = FastAPI()  # The real app lifespan is deliberately not imported/run.
    for router in [auth_router, news_router, public_router, admin_router]:
        app.include_router(router)

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def body(quantity=2):
    return {"eventId": "1", "items": [{"ticketTypeId": "1", "quantity": quantity}],
            "buyerName": "QA Buyer", "buyerEmail": "qa@example.com", "buyerPhone": "+255000000001"}


def create(client, key="qa-order-key-00000001", payload=None):
    return client.post("/api/tickets/orders", json=body() if payload is None else payload,
                       headers={"Idempotency-Key": key})


def owner(response):
    return {"Authorization": "Bearer " + response.json()["checkoutToken"]}


def admin(index=1):
    return {"Authorization": "Bearer " + create_access_token(index)}


@pytest.mark.parametrize("change", [
    {"items": []}, {"buyerEmail": "bad"}, {"buyerName": " "}, {"buyerPhone": "        "},
    {"items": [{"ticketTypeId": "1", "quantity": 0}]},
    {"items": [{"ticketTypeId": "1", "quantity": True}]},
    {"items": [{"ticketTypeId": "1", "quantity": 1}, {"ticketTypeId": "1", "quantity": 1}]},
])
def test_invalid_order_does_not_reserve_stock(system, change):
    client, engine = system
    assert create(client, payload={**body(), **change}).status_code == 422
    with Session(engine) as db:
        assert db.query(Order).count() == 0
        assert db.get(TicketType, 1).quantity_reserved == 0


def test_idempotent_replay_and_mismatched_payload(system):
    client, engine = system
    first = create(client)
    assert first.status_code == 200, first.text
    second = create(client)
    assert second.status_code == 200
    assert first.json()["order"]["id"] == second.json()["order"]["id"]
    assert first.json()["order"]["total"] == 2000
    assert create(client, payload=body(1)).status_code == 409
    with Session(engine) as db:
        assert db.query(Order).count() == 1
        assert db.get(TicketType, 1).quantity_reserved == 2


def test_required_idempotency_key_and_server_stock_limits(system):
    client, engine = system
    assert client.post("/api/tickets/orders", json=body()).status_code == 422
    assert create(client, key="short").status_code == 422
    assert create(client, payload=body(3)).status_code == 400
    with Session(engine) as db:
        db.get(TicketType, 1).quantity_total = 1
        db.commit()
    assert create(client).status_code == 409
    with Session(engine) as db:
        assert db.query(Order).count() == 0


def test_order_ownership_and_admin_token_separation(system):
    client, _ = system
    first = create(client)
    second = create(client, key="qa-order-key-00000002", payload=body(1))
    order_id = first.json()["order"]["id"]
    path = "/api/tickets/orders/" + order_id
    assert client.get(path).status_code == 401
    assert client.get(path, headers=owner(second)).status_code == 404
    assert client.get(path, headers=owner(first)).status_code == 200
    assert client.get(path, headers=admin(3)).status_code == 200
    assert client.get(path, headers=admin(2)).status_code == 403
    assert client.get("/api/admin/me", headers=owner(first)).status_code == 401
    assert client.get(path + "/tickets", headers=owner(first)).json()["tickets"] == []


def test_cancel_is_owner_only_and_releases_once(system):
    client, engine = system
    response = create(client)
    path = "/api/tickets/orders/" + response.json()["order"]["id"] + "/cancel"
    assert client.post(path).status_code == 401
    assert client.post(path, headers=admin(3)).status_code == 403
    for _ in range(2):
        cancelled = client.post(path, headers=owner(response))
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["status"] == "CANCELLED"
    with Session(engine) as db:
        assert db.get(TicketType, 1).quantity_reserved == 0


def test_expiry_releases_once_and_replay_does_not_recreate(system):
    client, engine = system
    response = create(client)
    order_id = int(response.json()["order"]["id"])
    with Session(engine) as db:
        db.get(Order, order_id).expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    for _ in range(2):
        status = client.get(f"/api/tickets/orders/{order_id}", headers=owner(response))
        assert status.json()["status"] == "EXPIRED"
    assert create(client).json()["order"]["id"] == str(order_id)
    with Session(engine) as db:
        assert db.query(Order).count() == 1
        assert db.get(TicketType, 1).quantity_reserved == 0


def test_public_draft_privacy_and_admin_metadata(system):
    client, _ = system
    assert client.get("/api/tickets/events/2").status_code == 404
    detail = client.get("/api/admin/tickets/events/1", headers=admin()).json()
    assert detail["event"]["publish_status"] == "published"
    assert detail["event"]["display_order"] == 3
    assert detail["tiers"][0]["quantity_total"] == 10
    assert detail["tiers"][0]["max_per_order"] == 2
    assert "quantity_total" not in client.get("/api/tickets/events/1").json()["tiers"][0]
    assert client.get("/api/tickets/payment-methods").json()["items"] == []


def test_inventory_cannot_drop_below_reserved(system):
    client, _ = system
    create(client)
    assert client.patch("/api/admin/tickets/tiers/1", json={"quantity_total": 1}, headers=admin()).status_code == 409


def test_roles_and_ticket_checkin_are_enforced(system):
    client, _ = system
    assert client.get("/api/admin/news", headers=admin(2)).status_code == 200
    assert client.get("/api/admin/news", headers=admin(3)).status_code == 403
    assert client.get("/api/admin/tickets/events", headers=admin(2)).status_code == 403
    assert client.get("/api/admin/tickets/events", headers=admin()).status_code == 200
    assert client.post("/api/tickets/check-in", json={"ticketToken": "qa-invalid"}).status_code == 401
    assert client.post("/api/tickets/check-in", json={"ticketToken": "qa-invalid"}, headers=admin(3)).status_code == 403
    assert client.post("/api/tickets/check-in", json={"ticketToken": "qa-invalid"}, headers=admin(4)).status_code == 200


def test_malformed_signed_subject_and_mock_payment_never_succeed(system):
    client, engine = system
    token = jwt.encode({"sub": "not-an-admin-id"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    assert client.get("/api/admin/me", headers={"Authorization": "Bearer " + token}).status_code == 401
    assert client.post("/api/tickets/payments", json={"orderId": "1", "provider": "mock"}).status_code == 409
    with Session(engine) as db:
        assert db.query(TicketPayment).count() == 0
        assert db.query(Ticket).count() == 0
