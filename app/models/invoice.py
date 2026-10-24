from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import enum_column, utcnow
from app.models.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("amount_due > 0", name="ck_invoices_amount_due_positive"),
        # Database backstop: an invoice can never be over-paid, whatever the application does.
        CheckConstraint("amount_paid >= 0 AND amount_paid <= amount_due", name="ck_invoices_paid_within_due"),
    )

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    currency = Column(String(3), nullable=False)
    status = Column(enum_column(InvoiceStatus), nullable=False, default=InvoiceStatus.ISSUED)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    subscription = relationship("Subscription", back_populates="invoices")
    customer = relationship("Customer")
    payment_attempts = relationship(
        "PaymentAttempt", back_populates="invoice", order_by="PaymentAttempt.id"
    )
    ledger_entries = relationship("LedgerEntry", back_populates="invoice")

    @property
    def amount_remaining(self) -> Decimal:
        return Decimal(self.amount_due) - Decimal(self.amount_paid)