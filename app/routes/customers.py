from fastapi import APIRouter, Depends, status

from app.dependencies import get_customer_service, get_ledger_service
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.ledger import LedgerEntryResponse
from app.services import CustomerService, LedgerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, service: CustomerService = Depends(get_customer_service)):
    return service.create_customer(payload)


@router.get("", response_model=list[CustomerResponse])
def list_customers(service: CustomerService = Depends(get_customer_service)):
    return service.list_customers()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, service: CustomerService = Depends(get_customer_service)):
    return service.get_customer(customer_id)


@router.get("/{customer_id}/ledger", response_model=list[LedgerEntryResponse])
def get_customer_ledger(customer_id: int, service: LedgerService = Depends(get_ledger_service)):
    return service.get_customer_ledger(customer_id)