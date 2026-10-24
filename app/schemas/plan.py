from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BillingCycle, PlanStatus


def _normalise_currency(value: str | None) -> str | None:
    if value is None:
        return value
    value = value.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise ValueError("currency must be a 3-letter code such as USD or INR")
    return value


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: str = "USD"
    status: PlanStatus = PlanStatus.ACTIVE

    _check_currency = field_validator("currency")(_normalise_currency)


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    billing_cycle: BillingCycle | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    currency: str | None = None
    status: PlanStatus | None = None

    _check_currency = field_validator("currency")(_normalise_currency)


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    billing_cycle: BillingCycle
    price: Decimal
    currency: str
    status: PlanStatus
    created_at: datetime
    updated_at: datetime