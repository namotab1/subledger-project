class DomainError(Exception):
    """Base class for business-rule errors.

    Services raise these instead of HTTP exceptions, so the service layer
    stays independent of FastAPI. main.py maps them to HTTP responses.
    """

    status_code = 400
    code = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    """The request is valid but conflicts with the current state of the data."""

    status_code = 409
    code = "conflict"


class BusinessRuleError(DomainError):
    """The request is well-formed but violates a business rule."""

    status_code = 422
    code = "business_rule_violation"


class AppendOnlyError(DomainError):
    status_code = 409
    code = "append_only_violation"