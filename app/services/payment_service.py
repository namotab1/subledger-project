from app.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models import Invoice, PaymentAttempt
from app.models.enums import InvoiceStatus, PaymentStatus
from app.repositories import InvoiceRepository, PaymentAttemptRepository
from app.schemas.payment import PaymentRecord
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService

PAYABLE_STATUSES = {InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE}


class PaymentService:
    """Owns: recording payment attempts, validating the amount, triggering the invoice update and ledger entry."""

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        payment_attempt_repo: PaymentAttemptRepository,
        ledger_service: LedgerService,
        invoice_service: InvoiceService,
    ):
        self.invoice_repo = invoice_repo
        self.payment_attempt_repo = payment_attempt_repo
        self.ledger_service = ledger_service
        self.invoice_service = invoice_service

    def record_payment(self, data: PaymentRecord) -> tuple[PaymentAttempt, Invoice]:
        # Lock the invoice row: two simultaneous payments cannot both pass the balance check.
        invoice = self.invoice_repo.get_by_id_for_update(data.invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {data.invoice_id} not found.")

        if invoice.status not in PAYABLE_STATUSES:
            raise ConflictError(f"Invoice {invoice.id} is {invoice.status.value} and cannot accept payments.")
        if data.currency != invoice.currency:
            raise BusinessRuleError(
                f"Payment currency {data.currency} does not match invoice currency {invoice.currency}."
            )

        is_success = data.status == PaymentStatus.SUCCESS
        if is_success and data.amount > invoice.amount_remaining:
            raise BusinessRuleError(
                f"Payment of {data.amount} exceeds the remaining unpaid amount of {invoice.amount_remaining}."
            )

        attempt = PaymentAttempt(
            invoice_id=invoice.id,
            amount=data.amount,
            currency=data.currency,
            status=data.status,
            provider_reference=data.provider_reference,
            failure_reason=None if is_success else (data.failure_reason or "No reason provided by the payment provider."),
        )
        self.payment_attempt_repo.add(attempt)

        if is_success:
            self.invoice_service.apply_successful_payment(invoice, data.amount)
            self.ledger_service.record_payment_success(invoice, attempt)
        else:
            # A failed payment never touches amount_paid or the invoice status.
            self.ledger_service.record_payment_failure(invoice, attempt)

        self.invoice_repo.commit()  # attempt + invoice update + ledger entry: all or nothing
        return attempt, invoice