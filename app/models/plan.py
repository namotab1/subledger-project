from sqlalchemy import CheckConstraint, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import enum_column, utcnow
from app.models.enums import BillingCycle, PlanStatus


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (CheckConstraint("price > 0", name="ck_plans_price_positive"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    billing_cycle = Column(enum_column(BillingCycle), nullable=False, default=BillingCycle.MONTHLY)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(enum_column(PlanStatus), nullable=False, default=PlanStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    subscriptions = relationship("Subscription", back_populates="plan")