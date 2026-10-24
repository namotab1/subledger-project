"""Dependency wiring: builds repositories and services and injects the shared DB session.

FastAPI calls get_db once per request and reuses it for every dependency below, so all
repositories in a request share one session (one transaction).
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import (
    CustomerRepository,
    InvoiceRepository,
    LedgerRepository,
    PaymentAttemptRepository,
    PlanRepository,
    SubscriptionRepository,
)
from app.services import (
    CustomerService,
    InvoiceService,
    LedgerService,
    PaymentService,
    PlanService,
    SubscriptionService,
)


# ---- repositories ----
def get_plan_repo(db: Session = Depends(get_db)) -> PlanRepository:
    return PlanRepository(db)


def get_customer_repo(db: Session = Depends(get_db)) -> CustomerRepository:
    return CustomerRepository(db)


def get_subscription_repo(db: Session = Depends(get_db)) -> SubscriptionRepository:
    return SubscriptionRepository(db)


def get_invoice_repo(db: Session = Depends(get_db)) -> InvoiceRepository:
    return InvoiceRepository(db)


def get_payment_attempt_repo(db: Session = Depends(get_db)) -> PaymentAttemptRepository:
    return PaymentAttemptRepository(db)


def get_ledger_repo(db: Session = Depends(get_db)) -> LedgerRepository:
    return LedgerRepository(db)


# ---- services ----
def get_plan_service(plan_repo: PlanRepository = Depends(get_plan_repo)) -> PlanService:
    return PlanService(plan_repo)


def get_customer_service(customer_repo: CustomerRepository = Depends(get_customer_repo)) -> CustomerService:
    return CustomerService(customer_repo)


def get_subscription_service(
    subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
    plan_repo: PlanRepository = Depends(get_plan_repo),
    customer_repo: CustomerRepository = Depends(get_customer_repo),
) -> SubscriptionService:
    return SubscriptionService(subscription_repo, plan_repo, customer_repo)


def get_ledger_service(
    ledger_repo: LedgerRepository = Depends(get_ledger_repo),
    customer_repo: CustomerRepository = Depends(get_customer_repo),
) -> LedgerService:
    return LedgerService(ledger_repo, customer_repo)


def get_invoice_service(
    subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
    plan_repo: PlanRepository = Depends(get_plan_repo),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repo),
    ledger_service: LedgerService = Depends(get_ledger_service),
) -> InvoiceService:
    return InvoiceService(subscription_repo, plan_repo, invoice_repo, ledger_service)


def get_payment_service(
    invoice_repo: InvoiceRepository = Depends(get_invoice_repo),
    payment_attempt_repo: PaymentAttemptRepository = Depends(get_payment_attempt_repo),
    ledger_service: LedgerService = Depends(get_ledger_service),
    invoice_service: InvoiceService = Depends(get_invoice_service),
) -> PaymentService:
    return PaymentService(invoice_repo, payment_attempt_repo, ledger_service, invoice_service)