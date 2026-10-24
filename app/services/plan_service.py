from decimal import Decimal

from app.exceptions import BusinessRuleError, NotFoundError
from app.models import Plan
from app.models.enums import PlanStatus
from app.repositories import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    """Owns: price and billing-cycle validation, plan status changes."""

    def __init__(self, plan_repo: PlanRepository):
        self.plan_repo = plan_repo

    def create_plan(self, data: PlanCreate) -> Plan:
        self._ensure_price_positive(data.price)
        plan = Plan(
            name=data.name.strip(),
            description=data.description,
            billing_cycle=data.billing_cycle,
            price=data.price,
            currency=data.currency,
            status=data.status,
        )
        self.plan_repo.add(plan)
        self.plan_repo.commit()
        return plan

    def get_plan(self, plan_id: int) -> Plan:
        plan = self.plan_repo.get_by_id(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {plan_id} not found.")
        return plan

    def list_plans(self, status: PlanStatus | None = None) -> list[Plan]:
        return self.plan_repo.list(status)

    def update_plan(self, plan_id: int, data: PlanUpdate) -> Plan:
        plan = self.get_plan(plan_id)
        changes = data.model_dump(exclude_unset=True)

        if "price" in changes:
            if changes["price"] is None:
                raise BusinessRuleError("price cannot be null.")
            self._ensure_price_positive(changes["price"])
        for required in ("name", "billing_cycle", "currency", "status"):
            if required in changes and changes[required] is None:
                raise BusinessRuleError(f"{required} cannot be null.")

        # Changing the price affects only invoices generated from now on:
        # existing invoices keep the amount_due they were issued with.
        for field, value in changes.items():
            setattr(plan, field, value)

        self.plan_repo.save(plan)
        self.plan_repo.commit()
        return plan

    @staticmethod
    def _ensure_price_positive(price: Decimal) -> None:
        if price <= 0:
            raise BusinessRuleError("Plan price must be greater than 0.")