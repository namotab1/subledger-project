from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import ConflictError


class BaseRepository:
    """Holds the shared session and the transaction helpers.

    Repositories only *flush* (so ids are populated). A service decides when the
    unit of work is complete and calls commit() once.
    """

    def __init__(self, db: Session):
        self.db = db

    def add(self, obj):
        self.db.add(obj)
        self._flush()
        return obj

    def save(self, obj):
        """Persist changes made to an object that is already tracked by the session."""
        self._flush()
        return obj

    def commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("The request conflicts with existing data.") from exc

    def rollback(self) -> None:
        self.db.rollback()

    def _flush(self) -> None:
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("The request conflicts with existing data.") from exc