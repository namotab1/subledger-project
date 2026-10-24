from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import InvoiceStatus, PaymentStatus
from app.schemas.invoice import InvoiceResponse


class PaymentRecord(BaseModel):
    invoice_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: str
    status: PaymentStatus
    provider_reference: str = Field(min_length=1, max_length=100)
    failure_reason: str | None = None  # only meaningful when status is "failed"

    @field_validator("currency")
    @classmethod
    def _check_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter code such as USD or INR")
        return value


class PaymentAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider_reference: str
    failure_reason: str | None
    created_at: datetime


class PaymentRecordResponse(BaseModel):
    payment_attempt: PaymentAttemptResponse
    invoice_status: InvoiceStatus
    invoice: InvoiceResponse