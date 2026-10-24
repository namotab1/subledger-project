from fastapi import APIRouter, Depends, status

from app.dependencies import get_plan_service
from app.models.enums import PlanStatus
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.services import PlanService

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreate, service: PlanService = Depends(get_plan_service)):
    return service.create_plan(payload)


@router.get("", response_model=list[PlanResponse])
def list_plans(status: PlanStatus | None = None, service: PlanService = Depends(get_plan_service)):
    return service.list_plans(status)


@router.patch("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, payload: PlanUpdate, service: PlanService = Depends(get_plan_service)):
    return service.update_plan(plan_id, payload)