from fastapi import APIRouter, Depends, status

from app.dependencies import get_invoice_service
from app.schemas.invoice import InvoiceDetailResponse, InvoiceGenerate, InvoiceResponse
from app.services import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/generate", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def generate_invoice(payload: InvoiceGenerate, service: InvoiceService = Depends(get_invoice_service)):
    return service.generate_invoice(payload)


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(invoice_id: int, service: InvoiceService = Depends(get_invoice_service)):
    return service.get_invoice(invoice_id)