from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, event
from sqlalchemy.orm import relationship

from app.db import Base
from app.exceptions import AppendOnlyError
from app.models.base import enum_column, utcnow
from app.models.enums import LedgerEntryType


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True, index=True)
    entry_type = Column(enum_column(LedgerEntryType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    # Points at the record that caused this entry, e.g. "invoice:12" or "payment_attempt:7".
    reference_id = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    customer = relationship("Customer", back_populates="ledger_entries")
    invoice = relationship("Invoice", back_populates="ledger_entries")


@event.listens_for(LedgerEntry, "before_update")
def _block_ledger_update(mapper, connection, target):
    raise AppendOnlyError("Ledger entries are append-only and cannot be modified.")


@event.listens_for(LedgerEntry, "before_delete")
def _block_ledger_delete(mapper, connection, target):
    raise AppendOnlyError("Ledger entries are append-only and cannot be deleted.")