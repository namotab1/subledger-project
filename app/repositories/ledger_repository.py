from app.exceptions import AppendOnlyError
from app.models import LedgerEntry
from app.repositories.base import BaseRepository


class LedgerRepository(BaseRepository):
    """Append-only by design: it exposes add() and read methods, and nothing that updates or deletes."""

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        return super().add(entry)

    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        return (
            self.db.query(LedgerEntry)
            .filter(LedgerEntry.customer_id == customer_id)
            .order_by(LedgerEntry.id)
            .all()
        )

    def list_for_invoice(self, invoice_id: int) -> list[LedgerEntry]:
        return (
            self.db.query(LedgerEntry)
            .filter(LedgerEntry.invoice_id == invoice_id)
            .order_by(LedgerEntry.id)
            .all()
        )

    def save(self, obj):
        raise AppendOnlyError("Ledger entries are append-only and cannot be modified.")