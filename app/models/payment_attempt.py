from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import enum_column, utcnow
from app.models.enums import PaymentStatus


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_payment_attempts_amount_positive"),)

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(enum_column(PaymentStatus), nullable=False)
    provider_reference = Column(String(100), nullable=False, index=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    invoice = relationship("Invoice", back_populates="payment_attempts")