# =========================
# backend/infrastructure/persistence/sql/position_baseline_repo_sql.py
# =========================
"""SQL implementation of PositionBaselineRepo."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from uuid import uuid4

from sqlalchemy import select, desc

from domain.ports.position_baseline_repo import PositionBaselineRepo
from infrastructure.persistence.sql.models import PositionBaselineModel


class PositionBaselineRepoSQL(PositionBaselineRepo):
    """SQL implementation of PositionBaselineRepo."""

    def __init__(self, session_factory):
        """
        Initialize SQL repository.

        Args:
            session_factory: Callable that returns a SQLAlchemy Session
        """
        self.session_factory = session_factory

    def save(self, baseline_data: Dict[str, Any]) -> str:
        """Save a position baseline record."""
        with self.session_factory() as session:
            # Generate ID if not provided
            baseline_id = baseline_data.get("id") or f"baseline_{uuid4().hex[:16]}"

            # Create new record (baselines are immutable, no updates)
            record = PositionBaselineModel(
                id=baseline_id, **{k: v for k, v in baseline_data.items() if k != "id"}
            )
            session.add(record)
            session.commit()
            return record.id

    def get_latest(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest baseline for a position."""
        with self.session_factory() as session:
            query = (
                select(PositionBaselineModel)
                .where(PositionBaselineModel.position_id == position_id)
                .order_by(desc(PositionBaselineModel.baseline_timestamp))
                .limit(1)
            )
            record = session.execute(query).scalar_one_or_none()
            if not record:
                return None
            return self._model_to_dict(record)

    def list_by_position(
        self,
        position_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List baseline records for a position, ordered by timestamp (newest first)."""
        with self.session_factory() as session:
            query = (
                select(PositionBaselineModel)
                .where(PositionBaselineModel.position_id == position_id)
                .order_by(desc(PositionBaselineModel.baseline_timestamp))
            )
            if limit:
                query = query.limit(limit)
            records = session.execute(query).scalars().all()
            return [self._model_to_dict(r) for r in records]

    def _model_to_dict(self, record: PositionBaselineModel) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        result = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name, None)
            # Convert datetime to ISO string for JSON serialization
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            result[column.name] = value
        return result
