from app.models import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository):
    def get_by_id(self, customer_id: int) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def get_by_email(self, email: str) -> Customer | None:
        return self.db.query(Customer).filter(Customer.email == email).first()

    def list(self) -> list[Customer]:
        return self.db.query(Customer).order_by(Customer.id).all()