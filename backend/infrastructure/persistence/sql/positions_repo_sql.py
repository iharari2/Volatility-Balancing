from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select, inspect, text
from sqlalchemy.engine import Engine

from domain.entities.position import Position
from domain.ports.positions_repo import PositionsRepo
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy
from .models import PositionModel


def _to_entity(m: PositionModel) -> Position:
    """SQL row -> domain entity."""
    # Safely get cash value - handle both None and missing attribute cases
    try:
        cash_value = getattr(m, "cash", None)
        if cash_value is None:
            cash_value = 0.0
        else:
            cash_value = float(cash_value)
    except (AttributeError, TypeError, ValueError):
        cash_value = 0.0

    return Position(
        id=m.id,
        tenant_id=m.tenant_id,
        portfolio_id=m.portfolio_id,
        asset_symbol=m.asset_symbol,
        qty=m.qty,
        cash=cash_value,  # Read cash from position (cash lives in PositionCell), handle NULL
        anchor_price=m.anchor_price,
        avg_cost=m.avg_cost,
        created_at=m.created_at,
        updated_at=m.updated_at,
        # Commission and dividend aggregates
        total_commission_paid=getattr(m, "total_commission_paid", 0.0) or 0.0,
        total_dividends_received=getattr(m, "total_dividends_received", 0.0) or 0.0,
        # Coalesce nullable policy columns to defaults
        order_policy=OrderPolicy(
            min_qty=m.op_min_qty or 0.0,
            min_notional=m.op_min_notional or 0.0,
            lot_size=m.op_lot_size or 0.0,
            qty_step=m.op_qty_step or 0.0,
            action_below_min=m.op_action_below_min or "hold",
        ),
        # Coalesce nullable guardrails columns to defaults
        guardrails=GuardrailPolicy(
            min_stock_alloc_pct=m.gr_min_stock_alloc_pct or 0.25,  # 25% default
            max_stock_alloc_pct=m.gr_max_stock_alloc_pct or 0.75,  # 75% default
            max_orders_per_day=m.gr_max_orders_per_day or 5,
        ),
    )


def _new_row_from_entity(p: Position) -> PositionModel:
    """Domain entity -> new SQL row (insert)."""
    return PositionModel(
        id=p.id,
        tenant_id=p.tenant_id,
        portfolio_id=p.portfolio_id,
        asset_symbol=p.asset_symbol,
        ticker=p.asset_symbol,  # Set ticker for backward compatibility with existing DB schema
        qty=p.qty,
        cash=p.cash,  # Cash lives in PositionCell (per target state model)
        anchor_price=p.anchor_price,
        avg_cost=p.avg_cost,
        total_commission_paid=p.total_commission_paid,
        total_dividends_received=p.total_dividends_received,
        status="RUNNING",  # Default status per usage model (can be changed to PAUSED)
        created_at=p.created_at,
        updated_at=p.updated_at,
        op_min_qty=p.order_policy.min_qty,
        op_min_notional=p.order_policy.min_notional,
        op_lot_size=p.order_policy.lot_size,
        op_qty_step=p.order_policy.qty_step,
        op_action_below_min=p.order_policy.action_below_min,
        gr_min_stock_alloc_pct=p.guardrails.min_stock_alloc_pct,
        gr_max_stock_alloc_pct=p.guardrails.max_stock_alloc_pct,
        gr_max_orders_per_day=p.guardrails.max_orders_per_day,
    )


def _apply_entity_to_row(row: PositionModel, p: Position) -> None:
    """Apply domain entity fields onto an existing SQL row (update)."""
    row.asset_symbol = p.asset_symbol
    row.ticker = p.asset_symbol  # Update ticker for backward compatibility
    row.qty = p.qty
    row.cash = p.cash  # Update cash (cash lives in PositionCell)
    row.anchor_price = p.anchor_price
    row.avg_cost = p.avg_cost
    row.total_commission_paid = p.total_commission_paid
    row.total_dividends_received = p.total_dividends_received
    row.updated_at = p.updated_at

    row.op_min_qty = p.order_policy.min_qty
    row.op_min_notional = p.order_policy.min_notional
    row.op_lot_size = p.order_policy.lot_size
    row.op_qty_step = p.order_policy.qty_step
    row.op_action_below_min = p.order_policy.action_below_min

    row.gr_min_stock_alloc_pct = p.guardrails.min_stock_alloc_pct
    row.gr_max_stock_alloc_pct = p.guardrails.max_stock_alloc_pct
    row.gr_max_orders_per_day = p.guardrails.max_orders_per_day


class SQLPositionsRepo(PositionsRepo):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sf = session_factory
        self._status_column_exists: Optional[bool] = None  # Cache column existence check

    def _check_status_column_exists(self, session: Session) -> bool:
        """Check if the status column exists in the positions table."""
        if self._status_column_exists is not None:
            return self._status_column_exists

        try:
            # Get the engine from the session
            engine: Engine = session.bind
            if engine is None:
                # Fallback: assume column doesn't exist to be safe
                self._status_column_exists = False
                return False

            # Check if column exists
            inspector = inspect(engine)
            columns = [col["name"] for col in inspector.get_columns("positions")]
            self._status_column_exists = "status" in columns
            return self._status_column_exists
        except Exception:
            # If we can't check, assume it doesn't exist to be safe
            self._status_column_exists = False
            return False

    def _create_model_from_row(self, row_tuple) -> PositionModel:
        """Create a PositionModel instance from a raw SQL row tuple (without status column)."""
        pos_model = PositionModel()
        pos_model.id = row_tuple[0]
        pos_model.tenant_id = row_tuple[1]
        pos_model.portfolio_id = row_tuple[2]
        pos_model.asset_symbol = row_tuple[3]
        pos_model.ticker = row_tuple[4]
        pos_model.qty = row_tuple[5]
        pos_model.cash = row_tuple[6]
        pos_model.anchor_price = row_tuple[7]
        pos_model.avg_cost = row_tuple[8]
        pos_model.op_min_qty = row_tuple[9]
        pos_model.op_min_notional = row_tuple[10]
        pos_model.op_lot_size = row_tuple[11]
        pos_model.op_qty_step = row_tuple[12]
        pos_model.op_action_below_min = row_tuple[13]
        pos_model.gr_min_stock_alloc_pct = row_tuple[14]
        pos_model.gr_max_stock_alloc_pct = row_tuple[15]
        pos_model.gr_max_orders_per_day = row_tuple[16]
        pos_model.total_commission_paid = row_tuple[17]
        pos_model.total_dividends_received = row_tuple[18]
        pos_model.created_at = row_tuple[19]
        pos_model.updated_at = row_tuple[20]
        return pos_model

    # --- Reads ---

    def get(self, tenant_id: str, portfolio_id: str, position_id: str) -> Optional[Position]:
        with self._sf() as s:
            status_exists = self._check_status_column_exists(s)

            if not status_exists:
                # Use raw SQL to select without status column
                raw_sql = text(
                    """
                    SELECT id, tenant_id, portfolio_id, asset_symbol, ticker, qty, cash, 
                           anchor_price, avg_cost, op_min_qty, op_min_notional, op_lot_size, 
                           op_qty_step, op_action_below_min, gr_min_stock_alloc_pct, 
                           gr_max_stock_alloc_pct, gr_max_orders_per_day, 
                           total_commission_paid, total_dividends_received, 
                           created_at, updated_at
                    FROM positions
                    WHERE id = :position_id AND tenant_id = :tenant_id AND portfolio_id = :portfolio_id
                """
                )
                result = s.execute(
                    raw_sql,
                    {
                        "position_id": position_id,
                        "tenant_id": tenant_id,
                        "portfolio_id": portfolio_id,
                    },
                )
                row_tuple = result.fetchone()
                if not row_tuple:
                    return None
                row = self._create_model_from_row(row_tuple)
                return _to_entity(row)

            # Normal query when status column exists
            try:
                stmt = select(PositionModel).where(
                    PositionModel.id == position_id,
                    PositionModel.tenant_id == tenant_id,
                    PositionModel.portfolio_id == portfolio_id,
                )
                row = s.execute(stmt).scalar_one_or_none()
                if not row:
                    return None
                return _to_entity(row)
            except Exception as e:
                error_msg = str(e)
                if "no such column" in error_msg.lower() and "status" in error_msg.lower():
                    self._status_column_exists = False
                    return self.get(tenant_id, portfolio_id, position_id)  # Retry
                raise

    def list_all(self, tenant_id: str, portfolio_id: str) -> List[Position]:
        """List all positions for a tenant and portfolio."""
        with self._sf() as s:
            status_exists = self._check_status_column_exists(s)

            # If status column doesn't exist, use raw SQL to select only existing columns
            if not status_exists:
                # Use raw SQL to select all columns except status
                raw_sql = text(
                    """
                    SELECT id, tenant_id, portfolio_id, asset_symbol, ticker, qty, cash, 
                           anchor_price, avg_cost, op_min_qty, op_min_notional, op_lot_size, 
                           op_qty_step, op_action_below_min, gr_min_stock_alloc_pct, 
                           gr_max_stock_alloc_pct, gr_max_orders_per_day, 
                           total_commission_paid, total_dividends_received, 
                           created_at, updated_at
                    FROM positions
                    WHERE tenant_id = :tenant_id AND portfolio_id = :portfolio_id
                    ORDER BY created_at DESC
                """
                )
                result = s.execute(raw_sql, {"tenant_id": tenant_id, "portfolio_id": portfolio_id})
                rows = [self._create_model_from_row(row) for row in result]
                return [_to_entity(r) for r in rows]

            # Normal query when status column exists
            try:
                stmt = (
                    select(PositionModel)
                    .where(
                        PositionModel.tenant_id == tenant_id,
                        PositionModel.portfolio_id == portfolio_id,
                    )
                    .order_by(PositionModel.created_at.desc())
                )
                rows = s.execute(stmt).scalars().all()
                return [_to_entity(r) for r in rows]
            except Exception as e:
                error_msg = str(e)
                if "no such column" in error_msg.lower() and "status" in error_msg.lower():
                    # Column doesn't exist, retry with raw SQL
                    self._status_column_exists = False
                    return self.list_all(
                        tenant_id, portfolio_id
                    )  # Recursive call with updated cache
                raise

    def get_by_asset(
        self, tenant_id: str, portfolio_id: str, asset_symbol: str
    ) -> Optional[Position]:
        """Get a position by asset symbol, scoped to tenant and portfolio."""
        with self._sf() as s:
            status_exists = self._check_status_column_exists(s)

            if not status_exists:
                # Use raw SQL to select without status column
                raw_sql = text(
                    """
                    SELECT id, tenant_id, portfolio_id, asset_symbol, ticker, qty, cash, 
                           anchor_price, avg_cost, op_min_qty, op_min_notional, op_lot_size, 
                           op_qty_step, op_action_below_min, gr_min_stock_alloc_pct, 
                           gr_max_stock_alloc_pct, gr_max_orders_per_day, 
                           total_commission_paid, total_dividends_received, 
                           created_at, updated_at
                    FROM positions
                    WHERE tenant_id = :tenant_id AND portfolio_id = :portfolio_id 
                          AND asset_symbol = :asset_symbol
                """
                )
                result = s.execute(
                    raw_sql,
                    {
                        "tenant_id": tenant_id,
                        "portfolio_id": portfolio_id,
                        "asset_symbol": asset_symbol,
                    },
                )
                row_tuple = result.fetchone()
                if not row_tuple:
                    return None
                row = self._create_model_from_row(row_tuple)
                return _to_entity(row)

            # Normal query when status column exists
            try:
                stmt = select(PositionModel).where(
                    PositionModel.tenant_id == tenant_id,
                    PositionModel.portfolio_id == portfolio_id,
                    PositionModel.asset_symbol == asset_symbol,
                )
                row = s.execute(stmt).scalar_one_or_none()
                if not row:
                    return None
                return _to_entity(row)
            except Exception as e:
                error_msg = str(e)
                if "no such column" in error_msg.lower() and "status" in error_msg.lower():
                    self._status_column_exists = False
                    return self.get_by_asset(tenant_id, portfolio_id, asset_symbol)  # Retry
                raise

    # --- Writes ---

    def save(self, position: Position) -> None:
        with self._sf() as s:
            status_exists = self._check_status_column_exists(s)

            # Check if row exists using appropriate method
            if not status_exists:
                # Use raw SQL to check if row exists
                check_sql = text(
                    """
                    SELECT id FROM positions
                    WHERE id = :position_id AND tenant_id = :tenant_id AND portfolio_id = :portfolio_id
                """
                )
                result = s.execute(
                    check_sql,
                    {
                        "position_id": position.id,
                        "tenant_id": position.tenant_id,
                        "portfolio_id": position.portfolio_id,
                    },
                )
                row_exists = result.fetchone() is not None
            else:
                # Normal query
                try:
                    stmt = select(PositionModel).where(
                        PositionModel.id == position.id,
                        PositionModel.tenant_id == position.tenant_id,
                        PositionModel.portfolio_id == position.portfolio_id,
                    )
                    row = s.execute(stmt).scalar_one_or_none()
                    row_exists = row is not None
                except Exception as e:
                    error_msg = str(e)
                    if "no such column" in error_msg.lower() and "status" in error_msg.lower():
                        self._status_column_exists = False
                        return self.save(position)  # Retry
                    raise

            if not row_exists:
                # Insert new row
                if not status_exists:
                    # Use raw SQL insert without status
                    insert_sql = text(
                        """
                        INSERT INTO positions (
                            id, tenant_id, portfolio_id, asset_symbol, ticker, qty, cash,
                            anchor_price, avg_cost, op_min_qty, op_min_notional, op_lot_size,
                            op_qty_step, op_action_below_min, gr_min_stock_alloc_pct,
                            gr_max_stock_alloc_pct, gr_max_orders_per_day,
                            total_commission_paid, total_dividends_received,
                            created_at, updated_at
                        ) VALUES (
                            :id, :tenant_id, :portfolio_id, :asset_symbol, :ticker, :qty, :cash,
                            :anchor_price, :avg_cost, :op_min_qty, :op_min_notional, :op_lot_size,
                            :op_qty_step, :op_action_below_min, :gr_min_stock_alloc_pct,
                            :gr_max_stock_alloc_pct, :gr_max_orders_per_day,
                            :total_commission_paid, :total_dividends_received,
                            :created_at, :updated_at
                        )
                    """
                    )
                    s.execute(
                        insert_sql,
                        {
                            "id": position.id,
                            "tenant_id": position.tenant_id,
                            "portfolio_id": position.portfolio_id,
                            "asset_symbol": position.asset_symbol,
                            "ticker": position.asset_symbol,
                            "qty": position.qty,
                            "cash": position.cash,
                            "anchor_price": position.anchor_price,
                            "avg_cost": position.avg_cost,
                            "op_min_qty": position.order_policy.min_qty,
                            "op_min_notional": position.order_policy.min_notional,
                            "op_lot_size": position.order_policy.lot_size,
                            "op_qty_step": position.order_policy.qty_step,
                            "op_action_below_min": position.order_policy.action_below_min,
                            "gr_min_stock_alloc_pct": position.guardrails.min_stock_alloc_pct,
                            "gr_max_stock_alloc_pct": position.guardrails.max_stock_alloc_pct,
                            "gr_max_orders_per_day": position.guardrails.max_orders_per_day,
                            "total_commission_paid": position.total_commission_paid,
                            "total_dividends_received": position.total_dividends_received,
                            "created_at": position.created_at,
                            "updated_at": position.updated_at,
                        },
                    )
                else:
                    # Normal insert with status
                    new_row = _new_row_from_entity(position)
                    s.add(new_row)
            else:
                # Update existing row
                if not status_exists:
                    # Use raw SQL update without status
                    update_sql = text(
                        """
                        UPDATE positions SET
                            asset_symbol = :asset_symbol, ticker = :ticker, qty = :qty, cash = :cash,
                            anchor_price = :anchor_price, avg_cost = :avg_cost,
                            op_min_qty = :op_min_qty, op_min_notional = :op_min_notional,
                            op_lot_size = :op_lot_size, op_qty_step = :op_qty_step,
                            op_action_below_min = :op_action_below_min,
                            gr_min_stock_alloc_pct = :gr_min_stock_alloc_pct,
                            gr_max_stock_alloc_pct = :gr_max_stock_alloc_pct,
                            gr_max_orders_per_day = :gr_max_orders_per_day,
                            total_commission_paid = :total_commission_paid,
                            total_dividends_received = :total_dividends_received,
                            updated_at = :updated_at
                        WHERE id = :id AND tenant_id = :tenant_id AND portfolio_id = :portfolio_id
                    """
                    )
                    s.execute(
                        update_sql,
                        {
                            "id": position.id,
                            "tenant_id": position.tenant_id,
                            "portfolio_id": position.portfolio_id,
                            "asset_symbol": position.asset_symbol,
                            "ticker": position.asset_symbol,
                            "qty": position.qty,
                            "cash": position.cash,
                            "anchor_price": position.anchor_price,
                            "avg_cost": position.avg_cost,
                            "op_min_qty": position.order_policy.min_qty,
                            "op_min_notional": position.order_policy.min_notional,
                            "op_lot_size": position.order_policy.lot_size,
                            "op_qty_step": position.order_policy.qty_step,
                            "op_action_below_min": position.order_policy.action_below_min,
                            "gr_min_stock_alloc_pct": position.guardrails.min_stock_alloc_pct,
                            "gr_max_stock_alloc_pct": position.guardrails.max_stock_alloc_pct,
                            "gr_max_orders_per_day": position.guardrails.max_orders_per_day,
                            "total_commission_paid": position.total_commission_paid,
                            "total_dividends_received": position.total_dividends_received,
                            "updated_at": position.updated_at,
                        },
                    )
                else:
                    # Normal update - get row and apply changes
                    stmt = select(PositionModel).where(
                        PositionModel.id == position.id,
                        PositionModel.tenant_id == position.tenant_id,
                        PositionModel.portfolio_id == position.portfolio_id,
                    )
                    row = s.execute(stmt).scalar_one_or_none()
                    if row:
                        _apply_entity_to_row(row, position)

            # Commit with error handling for missing status column
            try:
                s.commit()
            except Exception as commit_error:
                error_msg = str(commit_error)
                print(f"[DEBUG] Commit error in save(): {error_msg}")
                print(f"[DEBUG] Error type: {type(commit_error)}")

                # Check for status column error (various possible error messages)
                if (
                    ("no such column" in error_msg.lower() and "status" in error_msg.lower())
                    or ("table positions has no column named status" in error_msg.lower())
                    or (
                        "status" in error_msg.lower()
                        and ("column" in error_msg.lower() or "missing" in error_msg.lower())
                    )
                ):
                    # Status column doesn't exist, rollback and retry with raw SQL
                    print("[DEBUG] Detected missing status column, retrying with raw SQL")
                    s.rollback()
                    self._status_column_exists = False
                    # Retry the entire save operation
                    return self.save(position)
                # Re-raise if it's not a status column error
                print("[DEBUG] Re-raising error (not status column issue)")
                raise

    def create(
        self,
        tenant_id: str,
        portfolio_id: str,
        asset_symbol: str,
        qty: float,
        anchor_price: Optional[float] = None,
        avg_cost: Optional[float] = None,
        cash: float = 0.0,
    ) -> Position:
        """Create + persist a new Position (id + timestamps set here)."""
        now = datetime.now(timezone.utc)
        pos = Position(
            id=f"pos_{uuid4().hex[:8]}",
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            asset_symbol=asset_symbol,
            qty=qty,
            cash=cash,  # Cash lives in PositionCell
            anchor_price=anchor_price,
            avg_cost=avg_cost,
            created_at=now,
            updated_at=now,
        )
        self.save(pos)
        return pos

    def delete(self, tenant_id: str, portfolio_id: str, position_id: str) -> bool:
        """Delete a position by ID, scoped to tenant and portfolio. Returns True if deleted, False if not found."""
        with self._sf() as s:
            status_exists = self._check_status_column_exists(s)

            if not status_exists:
                # Use raw SQL to delete
                delete_sql = text(
                    """
                    DELETE FROM positions
                    WHERE id = :position_id AND tenant_id = :tenant_id AND portfolio_id = :portfolio_id
                """
                )
                result = s.execute(
                    delete_sql,
                    {
                        "position_id": position_id,
                        "tenant_id": tenant_id,
                        "portfolio_id": portfolio_id,
                    },
                )
                deleted = result.rowcount > 0
                s.commit()
                return deleted
            else:
                # Normal delete
                try:
                    stmt = select(PositionModel).where(
                        PositionModel.id == position_id,
                        PositionModel.tenant_id == tenant_id,
                        PositionModel.portfolio_id == portfolio_id,
                    )
                    row = s.execute(stmt).scalar_one_or_none()
                    if row is None:
                        return False
                    s.delete(row)
                    s.commit()
                    return True
                except Exception as e:
                    error_msg = str(e)
                    if "no such column" in error_msg.lower() and "status" in error_msg.lower():
                        self._status_column_exists = False
                        return self.delete(tenant_id, portfolio_id, position_id)  # Retry
                    raise

    def clear(self) -> None:
        """Wipe all positions (test helper / dev)."""
        with self._sf() as s:
            s.query(PositionModel).delete()
            s.commit()
