import calendar
from datetime import date

from app.models.enums import BillingCycle

_MONTHS_PER_CYCLE = {
    BillingCycle.MONTHLY: 1,
    BillingCycle.QUARTERLY: 3,
    BillingCycle.YEARLY: 12,
}


def add_months(start: date, months: int) -> date:
    """Add whole months, clamping to the last day of the target month (Jan 31 + 1 month = Feb 28/29)."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def period_end_for(cycle: BillingCycle, period_start: date) -> date:
    return add_months(period_start, _MONTHS_PER_CYCLE[cycle])