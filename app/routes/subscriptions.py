from fastapi import APIRouter, Depends, status

from app.dependencies import get_subscription_service
from app.models.enums import SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.services import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate, service: SubscriptionService = Depends(get_subscription_service)
):
    return service.create_subscription(payload)


@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    customer_id: int | None = None,
    status: SubscriptionStatus | None = None,
    service: SubscriptionService = Depends(get_subscription_service),
):
    return service.list_subscriptions(customer_id, status)


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(subscription_id: int, service: SubscriptionService = Depends(get_subscription_service)):
    return service.cancel_subscription(subscription_id)