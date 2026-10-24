from datetime import date, datetime, timezone

from app.exceptions import ConflictError, NotFoundError
from app.models import Subscription
from app.models.enums import PlanStatus, SubscriptionStatus
from app.repositories import CustomerRepository, PlanRepository, SubscriptionRepository
from app.schemas.subscription import SubscriptionCreate
from app.utils.billing import period_end_for


class SubscriptionService:
    """Owns: creating/cancelling subscriptions, the inactive-plan rule, the no-duplicate-active rule."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        customer_repo: CustomerRepository,
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.customer_repo = customer_repo

    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        if self.customer_repo.get_by_id(data.customer_id) is None:
            raise NotFoundError(f"Customer {data.customer_id} not found.")

        plan = self.plan_repo.get_by_id(data.plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {data.plan_id} not found.")
        if plan.status != PlanStatus.ACTIVE:
            raise ConflictError(f"Plan {plan.id} is inactive and cannot be subscribed to.")

        existing = self.subscription_repo.get_active_for_customer_and_plan(data.customer_id, data.plan_id)
        if existing is not None:
            raise ConflictError(
                f"Customer {data.customer_id} already has an active subscription (id {existing.id}) to plan {data.plan_id}."
            )

        start = data.start_date or date.today()
        subscription = Subscription(
            customer_id=data.customer_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,  # creating a subscription activates it
            start_date=start,
            current_period_start=start,
            current_period_end=period_end_for(plan.billing_cycle, start),
        )
        self.subscription_repo.add(subscription)  # partial unique index backs up the check above
        self.subscription_repo.commit()
        return subscription

    def cancel_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {subscription_id} not found.")
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise ConflictError(f"Subscription {subscription_id} is already cancelled.")

        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.now(timezone.utc)
        self.subscription_repo.save(subscription)
        self.subscription_repo.commit()
        return subscription

    def list_subscriptions(
        self, customer_id: int | None = None, status: SubscriptionStatus | None = None
    ) -> list[Subscription]:
        return self.subscription_repo.list(customer_id, status)