import pytest

from app.exceptions import AppendOnlyError
from app.models import LedgerEntry
from app.repositories import LedgerRepository

from tests.test_payments import pay


def ledger(client, customer_id):
    response = client.get(f"/customers/{customer_id}/ledger")
    assert response.status_code == 200
    return response.json()


def test_generating_an_invoice_writes_an_invoice_created_entry(client, billing_setup):
    entries = ledger(client, billing_setup["customer"]["id"])

    assert len(entries) == 1
    assert entries[0]["entry_type"] == "invoice_created"
    assert entries[0]["amount"] == "49.99"
    assert entries[0]["reference_id"] == f"invoice:{billing_setup['invoice']['id']}"
    assert entries[0]["invoice_id"] == billing_setup["invoice"]["id"]


def test_payments_write_success_and_failure_entries_traceable_by_reference_id(client, billing_setup):
    customer_id = billing_setup["customer"]["id"]
    invoice_id = billing_setup["invoice"]["id"]

    failed = pay(client, invoice_id, "49.99", status="failed", reference="pay_a").json()
    succeeded = pay(client, invoice_id, "49.99", reference="pay_b").json()

    entries = ledger(client, customer_id)
    assert [e["entry_type"] for e in entries] == ["invoice_created", "payment_failure", "payment_success"]
    assert entries[1]["reference_id"] == f"payment_attempt:{failed['payment_attempt']['id']}"
    assert entries[2]["reference_id"] == f"payment_attempt:{succeeded['payment_attempt']['id']}"


def test_rejected_payment_writes_no_ledger_entry(client, billing_setup):
    pay(client, billing_setup["invoice"]["id"], "500.00")  # exceeds the balance -> 422

    assert len(ledger(client, billing_setup["customer"]["id"])) == 1  # only invoice_created


def test_ledger_is_per_customer_and_unknown_customer_is_404(
    client, billing_setup, make_customer
):
    other = make_customer(email="other@example.com", name="Other")

    assert ledger(client, other["id"]) == []
    assert client.get("/customers/999/ledger").status_code == 404


def test_ledger_entries_cannot_be_modified_or_deleted(db_session, client, billing_setup):
    entry = db_session.query(LedgerEntry).first()

    entry.description = "tampered"
    with pytest.raises(AppendOnlyError):
        db_session.flush()
    db_session.rollback()

    db_session.delete(db_session.query(LedgerEntry).first())
    with pytest.raises(AppendOnlyError):
        db_session.flush()
    db_session.rollback()


def test_ledger_repository_exposes_no_way_to_save_changes(db_session):
    repo = LedgerRepository(db_session)

    with pytest.raises(AppendOnlyError):
        repo.save(object())