from app.models import Plan
from app.models.enums import PlanStatus
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository):
    def get_by_id(self, plan_id: int) -> Plan | None:
        return self.db.get(Plan, plan_id)

    def list(self, status: PlanStatus | None = None) -> list[Plan]:
        query = self.db.query(Plan)
        if status is not None:
            query = query.filter(Plan.status == status)
        return query.order_by(Plan.id).all()