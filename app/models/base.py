from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Enum as SAEnum


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def enum_column(enum_class: type[Enum]) -> SAEnum:
    """Store the enum's *value* ('active') as a plain VARCHAR, not a native DB enum."""
    return SAEnum(
        enum_class,
        native_enum=False,
        length=20,
        values_callable=lambda members: [m.value for m in members],
    )