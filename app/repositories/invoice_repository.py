from app.models import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository):
    def get_by_id(self, invoice_id: int) -> Invoice | None:
        return self.db.get(Invoice, invoice_id)

    def get_by_id_for_update(self, invoice_id: int) -> Invoice | None:
        """Fetch an invoice and lock its row (SELECT ... FOR UPDATE) until the transaction ends.

        Used when recording a payment, so two concurrent payments cannot both pass the
        remaining-balance check. SQLite ignores FOR UPDATE; PostgreSQL enforces it.
        """
        return (
            self.db.query(Invoice)
            .filter(Invoice.id == invoice_id)
            .with_for_update()
            .populate_existing()
            .first()
        )