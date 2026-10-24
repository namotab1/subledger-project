from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import LedgerEntryType


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    invoice_id: int | None
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    reference_id: str
    description: str | None
    created_at: datetime