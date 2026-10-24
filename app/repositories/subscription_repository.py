from app.models import Subscription
from app.models.enums import SubscriptionStatus
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository):
    def get_by_id(self, subscription_id: int) -> Subscription | None:
        return self.db.get(Subscription, subscription_id)

    def get_active_for_customer_and_plan(self, customer_id: int, plan_id: int) -> Subscription | None:
        return (
            self.db.query(Subscription)
            .filter(
                Subscription.customer_id == customer_id,
                Subscription.plan_id == plan_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .first()
        )

    def list(
        self, customer_id: int | None = None, status: SubscriptionStatus | None = None
    ) -> list[Subscription]:
        query = self.db.query(Subscription)
        if customer_id is not None:
            query = query.filter(Subscription.customer_id == customer_id)
        if status is not None:
            query = query.filter(Subscription.status == status)
        return query.order_by(Subscription.id).all()