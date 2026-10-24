from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import enum_column, utcnow
from app.models.enums import SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        # Database backstop for the rule "one active subscription per customer per plan".
        # A partial unique index only covers rows where status = 'active', so a
        # cancelled subscription never blocks a new one.
        Index(
            "uq_active_subscription_per_customer_plan",
            "customer_id",
            "plan_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(enum_column(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    start_date = Column(Date, nullable=False)
    current_period_start = Column(Date, nullable=False)
    current_period_end = Column(Date, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")