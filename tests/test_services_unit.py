"""Service tests with fake repositories and no database.

They show what dependency injection buys us: the business rules can be tested in isolation.
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.exceptions import BusinessRuleError, ConflictError
from app.models.enums import InvoiceStatus, PaymentStatus
from app.schemas.payment import PaymentRecord
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService


def make_invoice(amount_due="100.00", amount_paid="0.00", status=InvoiceStatus.ISSUED, currency="USD"):
    invoice = SimpleNamespace(
        id=1,
        customer_id=1,
        amount_due=Decimal(amount_due),
        amount_paid=Decimal(amount_paid),
        status=status,
        currency=currency,
    )
    invoice.amount_remaining = invoice.amount_due - invoice.amount_paid
    return invoice


def make_payment_service(invoice):
    invoice_repo = MagicMock()
    invoice_repo.get_by_id_for_update.return_value = invoice
    invoice_repo.save.side_effect = lambda obj: obj
    ledger_service = MagicMock()
    invoice_service = InvoiceService(MagicMock(), MagicMock(), invoice_repo, ledger_service, due_days=14)
    service = PaymentService(invoice_repo, MagicMock(), ledger_service, invoice_service)
    return service, invoice_repo, ledger_service


def payment(amount, status=PaymentStatus.SUCCESS, currency="USD"):
    return PaymentRecord(
        invoice_id=1, amount=Decimal(amount), currency=currency, status=status, provider_reference="ref"
    )


def test_partial_then_full_payment_status_transitions():
    invoice = make_invoice("100.00")
    service, _, _ = make_payment_service(invoice)

    service.record_payment(payment("40.00"))
    assert invoice.status == InvoiceStatus.PARTIALLY_PAID

    invoice.amount_remaining = invoice.amount_due - invoice.amount_paid
    service.record_payment(payment("60.00"))
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.amount_paid == Decimal("100.00")


def test_overpayment_is_rejected_before_anything_is_written():
    invoice = make_invoice("100.00", amount_paid="90.00")
    service, invoice_repo, ledger_service = make_payment_service(invoice)

    with pytest.raises(BusinessRuleError):
        service.record_payment(payment("20.00"))

    invoice_repo.commit.assert_not_called()
    ledger_service.record_payment_success.assert_not_called()
    assert invoice.amount_paid == Decimal("90.00")


def test_failed_payment_leaves_invoice_untouched_and_logs_a_failure():
    invoice = make_invoice("100.00")
    service, invoice_repo, ledger_service = make_payment_service(invoice)

    service.record_payment(payment("100.00", status=PaymentStatus.FAILED))

    assert invoice.amount_paid == Decimal("0.00")
    assert invoice.status == InvoiceStatus.ISSUED
    ledger_service.record_payment_failure.assert_called_once()
    ledger_service.record_payment_success.assert_not_called()
    invoice_repo.commit.assert_called_once()


def test_paid_invoice_cannot_accept_another_payment():
    invoice = make_invoice("100.00", amount_paid="100.00", status=InvoiceStatus.PAID)
    service, _, _ = make_payment_service(invoice)

    with pytest.raises(ConflictError):
        service.record_payment(payment("1.00"))