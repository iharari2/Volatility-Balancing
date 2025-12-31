# =========================
# backend/infrastructure/persistence/sql/evaluation_timeline_repo_sql.py
# =========================
"""Simplified SQL implementation of EvaluationTimelineRepo - focused on reliability."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import json

from sqlalchemy import select, and_, text, MetaData, Table

from domain.ports.evaluation_timeline_repo import EvaluationTimelineRepo
from infrastructure.persistence.sql.models import (
    PositionEvaluationTimelineModel,
)


class EvaluationTimelineRepoSQL(EvaluationTimelineRepo):
    """Simplified SQL implementation of EvaluationTimelineRepo."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, evaluation_data: Dict[str, Any]) -> str:
        """Save an evaluation timeline record - simplified and robust."""
        with self.session_factory() as session:
            try:
                # Generate ID if not provided
                evaluation_id = evaluation_data.get("id") or f"eval_{uuid4().hex[:16]}"

                # Reflect actual database schema
                metadata = MetaData()
                bind = session.get_bind()
                reflected_table = Table(
                    "position_evaluation_timeline", metadata, autoload_with=bind
                )
                actual_db_columns = {col.name for col in reflected_table.columns}

                # Filter data to only include columns that exist in database
                filtered_data = {}
                for k, v in evaluation_data.items():
                    if k == "id":
                        continue
                    if k not in actual_db_columns:
                        continue

                    # Convert types appropriately
                    if isinstance(v, (list, dict)):
                        filtered_data[k] = json.dumps(v) if v else None
                    elif isinstance(v, Decimal):
                        filtered_data[k] = float(v)
                    elif isinstance(v, bool):
                        filtered_data[k] = bool(v)
                    elif v is None:
                        filtered_data[k] = None
                    else:
                        # Ensure it's a plain Python value
                        filtered_data[k] = v

                # Handle action columns - they have DIFFERENT CHECK constraints!
                # action: IN ('BUY', 'SELL', 'HOLD', 'SKIP')
                # action_taken: IN ('NO_ACTION', 'ORDER_PROPOSED', 'ORDER_SUBMITTED', 'ORDER_EXECUTED')

                # Get action value for 'action' column
                action_value = None
                if "action" in filtered_data:
                    action_value = filtered_data["action"]
                elif "action" in evaluation_data:
                    action_value = evaluation_data["action"]

                # Normalize action value - MUST be uppercase for SQLite CHECK constraint
                if isinstance(action_value, bool):
                    action_value = "HOLD"
                elif action_value is None:
                    action_value = "HOLD"
                elif not isinstance(action_value, str):
                    action_value = str(action_value).upper().strip()
                else:
                    action_value = action_value.upper().strip()

                # Ensure valid constraint value for 'action' column
                valid_actions = ["BUY", "SELL", "HOLD", "SKIP"]
                if action_value not in valid_actions:
                    action_value = "HOLD"
                action_value = action_value.upper()

                # Get action_taken value - has DIFFERENT valid values
                action_taken_value = None
                if "action_taken" in filtered_data:
                    action_taken_value = filtered_data["action_taken"]
                elif "action_taken" in evaluation_data:
                    action_taken_value = evaluation_data["action_taken"]

                # Normalize action_taken value
                if isinstance(action_taken_value, bool):
                    action_taken_value = "NO_ACTION"
                elif action_taken_value is None:
                    action_taken_value = "NO_ACTION"
                elif not isinstance(action_taken_value, str):
                    action_taken_value = str(action_taken_value).upper().strip()
                else:
                    action_taken_value = action_taken_value.upper().strip()

                # Ensure valid constraint value for 'action_taken' column
                valid_action_taken = [
                    "NO_ACTION",
                    "ORDER_PROPOSED",
                    "ORDER_SUBMITTED",
                    "ORDER_EXECUTED",
                ]
                if action_taken_value not in valid_action_taken:
                    # Map action to action_taken if needed
                    if action_value in ["BUY", "SELL"]:
                        action_taken_value = "ORDER_PROPOSED"  # Default for trade actions
                    else:
                        action_taken_value = "NO_ACTION"  # Default for HOLD/SKIP
                action_taken_value = action_taken_value.upper()

                # Set action columns if they exist
                if "action" in actual_db_columns:
                    filtered_data["action"] = action_value
                if "action_taken" in actual_db_columns:
                    filtered_data["action_taken"] = action_taken_value

                # Ensure required NOT NULL columns have values
                # Based on schema validation: 18 NOT NULL fields (excluding PK)
                current_time = datetime.now(timezone.utc)
                market_price_raw_value = (
                    filtered_data.get("market_price_raw")
                    or filtered_data.get("effective_price")
                    or evaluation_data.get("effective_price")
                    or 0.0
                )

                # Get position values from evaluation_data if available
                position_qty_before_value = (
                    filtered_data.get("position_qty_before")
                    or evaluation_data.get("position_qty_before")
                    or evaluation_data.get("position_qty")
                    or 0.0
                )
                position_cash_before_value = (
                    filtered_data.get("position_cash_before")
                    or evaluation_data.get("position_cash_before")
                    or evaluation_data.get("position_cash")
                    or 0.0
                )
                position_dividend_receivable_before_value = (
                    filtered_data.get("position_dividend_receivable_before")
                    or evaluation_data.get("position_dividend_receivable_before")
                    or 0.0
                )

                # Calculate position_stock_value_before and position_total_value_before if not provided
                position_stock_value_before_value = filtered_data.get("position_stock_value_before")
                if position_stock_value_before_value is None:
                    # Calculate from qty and price
                    if position_qty_before_value and market_price_raw_value:
                        position_stock_value_before_value = float(
                            position_qty_before_value
                        ) * float(market_price_raw_value)
                    else:
                        position_stock_value_before_value = 0.0

                position_total_value_before_value = filtered_data.get("position_total_value_before")
                if position_total_value_before_value is None:
                    position_total_value_before_value = float(position_cash_before_value) + float(
                        position_stock_value_before_value
                    )

                # Build defaults dict - all 18 NOT NULL fields from schema validation
                # Based on: python scripts/validate_timeline_schema.py output
                required_defaults = {
                    "action_taken": action_taken_value,  # NOT NULL, CHECK: IN ('NO_ACTION', 'ORDER_PROPOSED', 'ORDER_SUBMITTED', 'ORDER_EXECUTED')
                    "allow_after_hours": filtered_data.get("allow_after_hours", True),
                    "anchor_reset_occurred": filtered_data.get("anchor_reset_occurred", False),
                    "evaluated_at": filtered_data.get(
                        "evaluated_at", filtered_data.get("timestamp", current_time)
                    ),
                    "is_fresh": filtered_data.get("is_fresh", True),
                    "is_inline": filtered_data.get("is_inline", True),
                    "is_market_hours": filtered_data.get("is_market_hours", True),
                    "market_price_raw": market_price_raw_value,
                    "mode": filtered_data.get("mode", evaluation_data.get("mode", "LIVE")),
                    "portfolio_id": filtered_data.get(
                        "portfolio_id", evaluation_data.get("portfolio_id", "")
                    ),
                    "position_cash_before": position_cash_before_value,
                    "position_dividend_receivable_before": position_dividend_receivable_before_value,
                    "position_id": filtered_data.get(
                        "position_id", evaluation_data.get("position_id", "")
                    ),
                    "position_qty_before": position_qty_before_value,
                    "position_stock_value_before": position_stock_value_before_value,
                    "position_total_value_before": position_total_value_before_value,
                    "tenant_id": filtered_data.get(
                        "tenant_id", evaluation_data.get("tenant_id", "default")
                    ),
                    "trigger_detected": filtered_data.get("trigger_detected", False),
                }

                # action is NULLABLE, but set it if provided
                if "action" in actual_db_columns and action_value:
                    filtered_data["action"] = action_value

                # Dynamically check for other NOT NULL columns and provide defaults
                for col in reflected_table.columns:
                    col_name = col.name
                    if col_name == "id":
                        continue
                    # Check if column is NOT NULL
                    try:
                        is_nullable = getattr(col, "nullable", True)
                        if (
                            not is_nullable
                            and col_name not in filtered_data
                            and col_name not in required_defaults
                        ):
                            # Provide a default based on column type
                            if isinstance(
                                col.type,
                                (
                                    type(reflected_table.c.timestamp.type),
                                    type(reflected_table.c.evaluated_at.type),
                                ),
                            ):
                                required_defaults[col_name] = current_time
                            elif isinstance(
                                col.type, type(reflected_table.c.is_market_hours.type)
                            ):  # Boolean
                                required_defaults[col_name] = False
                            elif isinstance(
                                col.type, type(reflected_table.c.market_price_raw.type)
                            ):  # Float
                                required_defaults[col_name] = 0.0
                            elif isinstance(
                                col.type, type(reflected_table.c.tenant_id.type)
                            ):  # String
                                required_defaults[col_name] = ""
                    except Exception:
                        pass  # Skip if we can't determine

                # Apply defaults for missing required columns
                for col_name, default_value in required_defaults.items():
                    if col_name in actual_db_columns and col_name not in filtered_data:
                        filtered_data[col_name] = default_value

                # Build INSERT statement - ensure action_taken is always included (it's NOT NULL)
                columns_set = set(filtered_data.keys())
                # Force include action_taken if it exists in DB (it's NOT NULL)
                if "action_taken" in actual_db_columns:
                    columns_set.add("action_taken")
                # action is nullable, but include it if we have a value
                if "action" in actual_db_columns and action_value:
                    columns_set.add("action")

                columns = ["id"] + sorted([k for k in columns_set if k in actual_db_columns])
                placeholders = [f":{col}" for col in columns]

                # Build params dict
                params = {"id": evaluation_id}
                for k, v in filtered_data.items():
                    if k in actual_db_columns:
                        params[k] = v

                # CRITICAL: Ensure action_taken is always in params (it's NOT NULL)
                # action_taken has different CHECK constraint than action!
                if "action_taken" in actual_db_columns:
                    params["action_taken"] = action_taken_value
                    if "action_taken" not in filtered_data:
                        filtered_data["action_taken"] = action_taken_value

                # action is nullable, but set it if we have a value
                if "action" in actual_db_columns and action_value:
                    params["action"] = action_value
                    if "action" not in filtered_data:
                        filtered_data["action"] = action_value

                # Execute INSERT
                sql = f"INSERT INTO position_evaluation_timeline ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                print(f"📝 Executing INSERT with {len(columns)} columns, action='{action_value}'")
                try:
                    session.execute(text(sql), params)
                    session.commit()
                    print(f"✅✅✅ Timeline record saved successfully! ID: {evaluation_id}")
                    return evaluation_id
                except Exception as insert_error:
                    print(f"❌ INSERT failed: {insert_error}")
                    print(f"   SQL: {sql[:200]}...")
                    print(f"   Action value: {action_value} (type: {type(action_value)})")
                    print(f"   Params keys: {list(params.keys())[:10]}...")
                    raise

            except Exception as e:
                session.rollback()
                import traceback

                error_msg = str(e).lower()
                print("❌❌❌ Timeline save failed with exception:")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                print("   Full traceback:")
                print(traceback.format_exc())
                # If it's a schema issue, try a simpler approach
                if "no such column" in error_msg or "check constraint" in error_msg:
                    print("⚠️  Attempting fallback save with minimal fields...")
                    # Try to save with minimal required fields only
                    try:
                        # Re-reflect to get fresh column list
                        metadata2 = MetaData()
                        bind2 = session.get_bind()
                        reflected_table2 = Table(
                            "position_evaluation_timeline", metadata2, autoload_with=bind2
                        )
                        actual_db_columns2 = {col.name for col in reflected_table2.columns}

                        # Get market_price_raw from effective_price if available
                        market_price_raw_minimal = (
                            evaluation_data.get("market_price_raw")
                            or evaluation_data.get("effective_price")
                            or 0.0
                        )
                        if isinstance(market_price_raw_minimal, Decimal):
                            market_price_raw_minimal = float(market_price_raw_minimal)

                        position_qty_before_minimal = (
                            evaluation_data.get("position_qty_before")
                            or evaluation_data.get("position_qty")
                            or 0.0
                        )
                        if isinstance(position_qty_before_minimal, Decimal):
                            position_qty_before_minimal = float(position_qty_before_minimal)

                        position_cash_before_minimal = (
                            evaluation_data.get("position_cash_before")
                            or evaluation_data.get("position_cash")
                            or 0.0
                        )
                        if isinstance(position_cash_before_minimal, Decimal):
                            position_cash_before_minimal = float(position_cash_before_minimal)

                        # Calculate derived values for minimal save
                        position_stock_value_before_minimal = position_qty_before_minimal * float(
                            market_price_raw_minimal
                        )
                        position_total_value_before_minimal = (
                            position_cash_before_minimal + position_stock_value_before_minimal
                        )

                        # Map action to action_taken (different CHECK constraints!)
                        if action_value and action_value in ["BUY", "SELL"]:
                            action_taken_minimal = "ORDER_PROPOSED"
                        else:
                            action_taken_minimal = "NO_ACTION"

                        minimal_data = {
                            "id": evaluation_id,
                            "tenant_id": evaluation_data.get("tenant_id", "default"),
                            "portfolio_id": evaluation_data.get("portfolio_id", ""),
                            "position_id": evaluation_data.get("position_id", ""),
                            "timestamp": evaluation_data.get(
                                "timestamp", datetime.now(timezone.utc)
                            ),
                            "evaluated_at": evaluation_data.get(
                                "timestamp", datetime.now(timezone.utc)
                            ),
                            "market_price_raw": market_price_raw_minimal,
                            "position_qty_before": position_qty_before_minimal,
                            "position_cash_before": position_cash_before_minimal,
                            "position_dividend_receivable_before": 0.0,
                            "position_stock_value_before": position_stock_value_before_minimal,
                            "position_total_value_before": position_total_value_before_minimal,
                            "mode": evaluation_data.get("mode", "LIVE"),
                            "is_market_hours": True,
                            "is_fresh": True,
                            "is_inline": True,
                            "allow_after_hours": True,
                            "anchor_reset_occurred": False,
                            "trigger_detected": False,
                            "action_taken": action_taken_minimal,  # Must be: NO_ACTION, ORDER_PROPOSED, ORDER_SUBMITTED, or ORDER_EXECUTED
                        }

                        # action is nullable, but include it if we have a value
                        if action_value:
                            minimal_data["action"] = action_value

                        # Only include columns that exist
                        minimal_filtered = {
                            k: v for k, v in minimal_data.items() if k in actual_db_columns2
                        }
                        if "id" in minimal_filtered:
                            minimal_id = minimal_filtered.pop("id")
                        else:
                            minimal_id = evaluation_id

                        # Ensure action_taken is always set (it's NOT NULL with different CHECK constraint)
                        if "action_taken" in actual_db_columns2:
                            # action_taken_minimal is already set in minimal_data above
                            if "action_taken" not in minimal_filtered:
                                minimal_filtered["action_taken"] = action_taken_minimal

                        minimal_columns = sorted(minimal_filtered.keys())
                        minimal_placeholders = [f":{col}" for col in minimal_columns]
                        minimal_params = {"id": minimal_id, **minimal_filtered}

                        minimal_sql = f"INSERT INTO position_evaluation_timeline (id, {', '.join(minimal_columns)}) VALUES (:id, {', '.join(minimal_placeholders)})"
                        session.execute(text(minimal_sql), minimal_params)
                        session.commit()
                        print("✅ Saved timeline record with minimal fields")
                        return minimal_id
                    except Exception as e2:
                        print(f"❌ Failed to save timeline record even with minimal fields: {e2}")
                        raise
                else:
                    raise

    def get_by_id(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get an evaluation record by ID."""
        with self.session_factory() as session:
            record = session.get(PositionEvaluationTimelineModel, evaluation_id)
            if not record:
                return None
            return self._model_to_dict(record)

    def list_by_position(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        mode: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List evaluation records for a position."""
        try:
            with self.session_factory() as session:
                # Use raw SQL to avoid ORM model column mismatches
                metadata = MetaData()
                bind = session.get_bind()
                reflected_table = Table(
                    "position_evaluation_timeline", metadata, autoload_with=bind
                )
                actual_db_columns = {col.name for col in reflected_table.columns}

                # Build WHERE clause
                where_clauses = [
                    "tenant_id = :tenant_id",
                    "portfolio_id = :portfolio_id",
                    "position_id = :position_id",
                ]
                params = {
                    "tenant_id": tenant_id,
                    "portfolio_id": portfolio_id,
                    "position_id": position_id,
                }

                if mode:
                    where_clauses.append("mode = :mode")
                    params["mode"] = mode

                # Determine timestamp column name - prefer evaluated_at, fallback to timestamp
                timestamp_col = None
                if "evaluated_at" in actual_db_columns:
                    timestamp_col = "evaluated_at"
                elif "timestamp" in actual_db_columns:
                    timestamp_col = "timestamp"

                if start_date and timestamp_col:
                    where_clauses.append(f"{timestamp_col} >= :start_date")
                    params["start_date"] = start_date

                if end_date and timestamp_col:
                    where_clauses.append(f"{timestamp_col} <= :end_date")
                    params["end_date"] = end_date

                # Build SELECT with only columns that exist
                columns_str = ", ".join(sorted(actual_db_columns))
                where_str = " AND ".join(where_clauses)

                # Determine ordering column - use same logic as timestamp_col
                order_by_col = timestamp_col if timestamp_col else "id"

                sql = f"SELECT {columns_str} FROM position_evaluation_timeline WHERE {where_str} ORDER BY {order_by_col} DESC"

                if limit:
                    sql += " LIMIT :limit"
                    params["limit"] = limit

                result = session.execute(text(sql), params)
                rows = result.fetchall()

                # Convert rows to dicts
                records = []
                for row in rows:
                    record = {}
                    for i, col_name in enumerate(sorted(actual_db_columns)):
                        value = row[i]
                        # Handle JSON columns
                        if isinstance(value, str) and col_name in [
                            "price_validation_rejections",
                            "price_validation_warnings",
                            "evaluation_details",
                            "market_data_details",
                            "strategy_state_details",
                            "execution_details",
                        ]:
                            try:
                                value = json.loads(value)
                            except Exception:
                                pass
                        record[col_name] = value
                    records.append(record)

                return records
        except Exception as e:
            error_msg = str(e).lower()
            if "no such column" in error_msg or "operationalerror" in error_msg:
                print(f"⚠️  Schema mismatch in list_by_position: {e}")
                return []
            raise

    def list_by_portfolio(
        self,
        tenant_id: str,
        portfolio_id: str,
        mode: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List evaluation records for a portfolio."""
        with self.session_factory() as session:
            query = select(PositionEvaluationTimelineModel).where(
                and_(
                    PositionEvaluationTimelineModel.tenant_id == tenant_id,
                    PositionEvaluationTimelineModel.portfolio_id == portfolio_id,
                )
            )

            if mode:
                query = query.where(PositionEvaluationTimelineModel.mode == mode)

            if start_date:
                query = query.where(PositionEvaluationTimelineModel.timestamp >= start_date)

            if end_date:
                query = query.where(PositionEvaluationTimelineModel.timestamp <= end_date)

            query = query.order_by(PositionEvaluationTimelineModel.timestamp.desc())

            if limit:
                query = query.limit(limit)

            records = session.execute(query).scalars().all()
            return [self._model_to_dict(r) for r in records]

    def list_by_trace_id(self, trace_id: str) -> List[Dict[str, Any]]:
        """List all evaluation records for a trace_id."""
        with self.session_factory() as session:
            query = (
                select(PositionEvaluationTimelineModel)
                .where(PositionEvaluationTimelineModel.trace_id == trace_id)
                .order_by(PositionEvaluationTimelineModel.timestamp.asc())
            )

            records = session.execute(query).scalars().all()
            return [self._model_to_dict(r) for r in records]

    def list_by_simulation_run(
        self,
        simulation_run_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List evaluation records for a simulation run."""
        with self.session_factory() as session:
            query = (
                select(PositionEvaluationTimelineModel)
                .where(PositionEvaluationTimelineModel.simulation_run_id == simulation_run_id)
                .order_by(PositionEvaluationTimelineModel.timestamp.asc())
            )

            if limit:
                query = query.limit(limit)

            records = session.execute(query).scalars().all()
            return [self._model_to_dict(r) for r in records]

    def _model_to_dict(self, record) -> Dict[str, Any]:
        """Convert ORM model to dictionary."""
        result = {}
        for col in record.__table__.columns:
            value = getattr(record, col.name, None)
            # Handle JSON columns
            if isinstance(value, str) and col.type.python_type in (dict, list):
                try:
                    value = json.loads(value)
                except Exception:
                    pass
            result[col.name] = value
        return result
