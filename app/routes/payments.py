from fastapi import APIRouter, Depends, status

from app.dependencies import get_payment_service
from app.schemas.payment import PaymentRecord, PaymentRecordResponse
from app.services import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/record", response_model=PaymentRecordResponse, status_code=status.HTTP_201_CREATED)
def record_payment(payload: PaymentRecord, service: PaymentService = Depends(get_payment_service)):
    attempt, invoice = service.record_payment(payload)
    return PaymentRecordResponse(
        payment_attempt=attempt,
        invoice_status=invoice.status,
        invoice=invoice,
    )