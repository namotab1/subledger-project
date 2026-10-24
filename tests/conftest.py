import os

# Tests always run on in-memory SQLite, never on the real database.
# This must be set before any app module is imported.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers every model on Base)
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory database for the whole test
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- small helpers that go through the real API ----------
@pytest.fixture()
def make_plan(client):
    def _make(name="Pro", price="49.99", billing_cycle="monthly", currency="USD", status="active"):
        response = client.post(
            "/plans",
            json={"name": name, "price": price, "billing_cycle": billing_cycle, "currency": currency, "status": status},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_customer(client):
    def _make(email="alice@example.com", name="Alice"):
        response = client.post("/customers", json={"name": name, "email": email, "company_name": "Acme"})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_subscription(client):
    def _make(customer_id, plan_id, start_date=None):
        body = {"customer_id": customer_id, "plan_id": plan_id}
        if start_date:
            body["start_date"] = start_date
        response = client.post("/subscriptions", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_invoice(client):
    def _make(subscription_id):
        response = client.post("/invoices/generate", json={"subscription_id": subscription_id})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def billing_setup(make_plan, make_customer, make_subscription, make_invoice):
    """A plan, a customer, an active subscription and one issued invoice (49.99 USD)."""
    plan = make_plan(price="49.99")
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"])
    invoice = make_invoice(subscription["id"])
    return {"plan": plan, "customer": customer, "subscription": subscription, "invoice": invoice}