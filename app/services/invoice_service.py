from datetime import timedelta
from decimal import Decimal

from app.config import get_settings
from app.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models import Invoice
from app.models.enums import InvoiceStatus, SubscriptionStatus
from app.repositories import InvoiceRepository, PlanRepository, SubscriptionRepository
from app.schemas.invoice import InvoiceGenerate
from app.services.ledger_service import LedgerService


class InvoiceService:
    """Owns: generating invoices, calculating amount_due, and moving invoice status after a payment."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        invoice_repo: InvoiceRepository,
        ledger_service: LedgerService,
        due_days: int | None = None,
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.invoice_repo = invoice_repo
        self.ledger_service = ledger_service
        self.due_days = due_days if due_days is not None else get_settings().invoice_due_days

    def generate_invoice(self, data: InvoiceGenerate) -> Invoice:
        subscription = self.subscription_repo.get_by_id(data.subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {data.subscription_id} not found.")
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ConflictError(f"Subscription {subscription.id} is not active; no invoice can be generated.")

        plan = self.plan_repo.get_by_id(subscription.plan_id)
        if plan is None:  # cannot happen with a foreign key, but fail loudly rather than guess
            raise NotFoundError(f"Plan {subscription.plan_id} not found.")

        period_start = data.period_start or subscription.current_period_start
        period_end = data.period_end or subscription.current_period_end

        # The invoice stores a snapshot of the plan price *now*. Later price changes do not touch it.
        invoice = Invoice(
            subscription_id=subscription.id,
            customer_id=subscription.customer_id,
            amount_due=plan.price,
            amount_paid=Decimal("0.00"),
            currency=plan.currency,
            status=InvoiceStatus.ISSUED,
            period_start=period_start,
            period_end=period_end,
            due_date=period_start + timedelta(days=self.due_days),
        )
        self.invoice_repo.add(invoice)
        self.ledger_service.record_invoice_created(invoice)
        self.invoice_repo.commit()  # invoice and ledger entry are saved together, or not at all
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found.")
        return invoice

    def apply_successful_payment(self, invoice: Invoice, amount: Decimal) -> Invoice:
        """Add a successful payment to the invoice and move it to partially_paid or paid.

        The caller (PaymentService) is responsible for having validated the amount; this
        method re-checks the invariant so the rule cannot be bypassed by another caller.
        """
        if amount <= 0:
            raise BusinessRuleError("Payment amount must be greater than 0.")
        if amount > invoice.amount_remaining:
            raise BusinessRuleError("Payment exceeds the remaining unpaid amount on the invoice.")

        invoice.amount_paid = Decimal(invoice.amount_paid) + amount
        if invoice.amount_paid >= invoice.amount_due:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        return self.invoice_repo.save(invoice)