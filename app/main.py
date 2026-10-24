from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import init_db
from app.exceptions import DomainError
from app.routes import customers, invoices, payments, plans, subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # creates tables on startup (no migration tool in the base version)
    yield


app = FastAPI(
    title=get_settings().app_name,
    description="A simplified SaaS subscription and billing backend.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Translate business-rule errors raised by services into HTTP responses."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "detail": exc.message})


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(plans.router)
app.include_router(customers.router)
app.include_router(subscriptions.router)
app.include_router(invoices.router)
app.include_router(payments.router)