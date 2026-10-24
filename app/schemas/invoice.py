from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from app.models.enums import InvoiceStatus, PaymentStatus


class InvoiceGenerate(BaseModel):
    subscription_id: int
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def _check_period(self) -> "InvoiceGenerate":
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("Provide both period_start and period_end, or neither.")
        if self.period_start and self.period_end and self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start.")
        return self


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    customer_id: int
    amount_due: Decimal
    amount_paid: Decimal
    currency: str
    status: InvoiceStatus
    period_start: date
    period_end: date
    due_date: date
    created_at: datetime

    @computed_field
    @property
    def amount_remaining(self) -> Decimal:
        return self.amount_due - self.amount_paid


class InvoicePaymentAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider_reference: str
    failure_reason: str | None
    created_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    payment_attempts: list[InvoicePaymentAttempt] = []