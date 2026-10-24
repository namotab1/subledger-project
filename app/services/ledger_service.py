from app.exceptions import NotFoundError
from app.models import Invoice, LedgerEntry, PaymentAttempt
from app.models.enums import LedgerEntryType
from app.repositories import CustomerRepository, LedgerRepository


def invoice_reference(invoice_id: int) -> str:
    return f"invoice:{invoice_id}"


def payment_attempt_reference(attempt_id: int) -> str:
    return f"payment_attempt:{attempt_id}"


class LedgerService:
    """Owns: creating append-only ledger entries and reading a customer's ledger history.

    It never commits: the calling service commits the whole unit of work, so a ledger
    entry is saved together with (or not at all without) the action it records.
    """

    def __init__(self, ledger_repo: LedgerRepository, customer_repo: CustomerRepository):
        self.ledger_repo = ledger_repo
        self.customer_repo = customer_repo

    def record_invoice_created(self, invoice: Invoice) -> LedgerEntry:
        return self._add(
            invoice,
            LedgerEntryType.INVOICE_CREATED,
            invoice.amount_due,
            invoice_reference(invoice.id),
            f"Invoice {invoice.id} issued for {invoice.period_start} to {invoice.period_end}.",
        )

    def record_payment_success(self, invoice: Invoice, attempt: PaymentAttempt) -> LedgerEntry:
        return self._add(
            invoice,
            LedgerEntryType.PAYMENT_SUCCESS,
            attempt.amount,
            payment_attempt_reference(attempt.id),
            f"Payment {attempt.provider_reference} succeeded for invoice {invoice.id}.",
        )

    def record_payment_failure(self, invoice: Invoice, attempt: PaymentAttempt) -> LedgerEntry:
        return self._add(
            invoice,
            LedgerEntryType.PAYMENT_FAILURE,
            attempt.amount,
            payment_attempt_reference(attempt.id),
            f"Payment {attempt.provider_reference} failed for invoice {invoice.id}: {attempt.failure_reason}",
        )

    def get_customer_ledger(self, customer_id: int) -> list[LedgerEntry]:
        if self.customer_repo.get_by_id(customer_id) is None:
            raise NotFoundError(f"Customer {customer_id} not found.")
        return self.ledger_repo.list_for_customer(customer_id)

    def _add(self, invoice, entry_type, amount, reference_id, description) -> LedgerEntry:
        entry = LedgerEntry(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=entry_type,
            amount=amount,
            currency=invoice.currency,
            reference_id=reference_id,
            description=description,
        )
        return self.ledger_repo.add(entry)