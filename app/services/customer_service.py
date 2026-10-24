from app.exceptions import ConflictError, NotFoundError
from app.models import Customer
from app.repositories import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    """Owns: customer creation, email uniqueness, customer lookup."""

    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    def create_customer(self, data: CustomerCreate) -> Customer:
        email = str(data.email).strip().lower()
        if self.customer_repo.get_by_email(email) is not None:
            raise ConflictError(f"A customer with email '{email}' already exists.")

        customer = Customer(name=data.name.strip(), email=email, company_name=data.company_name)
        self.customer_repo.add(customer)  # the unique index is the backstop for race conditions
        self.customer_repo.commit()
        return customer

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found.")
        return customer

    def list_customers(self) -> list[Customer]:
        return self.customer_repo.list()