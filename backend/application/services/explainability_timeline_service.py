# backend/application/services/explainability_timeline_service.py
"""
Explainability Timeline Service - Builds unified timeline view for live and simulation data.

This service transforms raw evaluation timeline data into the explainability format,
supporting daily aggregation, filtering, pagination, and order/trade enrichment.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

from application.dto.explainability import ExplainabilityRow, ExplainabilityTimeline
from domain.ports.orders_repo import OrdersRepo
from domain.ports.trades_repo import TradesRepo


logger = logging.getLogger(__name__)


class ExplainabilityTimelineService:
    """
    Service for building explainability timeline views.

    Transforms data from:
    - Live trading: position_evaluation_timeline table
    - Simulation: simulation result time_series_data

    Supports:
    - Daily aggregation (show 1 row per day if no action, all action rows if any)
    - Action filtering (BUY/SELL/HOLD/SKIP)
    - Order status filtering
    - Date range filtering
    - Pagination (offset/limit with total count)
    - Order/trade enrichment (joins evaluation data with Order and Trade entities)
    """

    def __init__(
        self,
        orders_repo: Optional[OrdersRepo] = None,
        trades_repo: Optional[TradesRepo] = None,
    ):
        self._orders_repo = orders_repo
        self._trades_repo = trades_repo

    def build_from_live_timeline(
        self,
        evaluation_records: List[Dict[str, Any]],
        position_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> List[ExplainabilityRow]:
        """
        Build explainability rows from live timeline records.

        Args:
            evaluation_records: List of records from position_evaluation_timeline
            position_id: Position ID for metadata
            portfolio_id: Portfolio ID for metadata
            symbol: Asset symbol for metadata

        Returns:
            List of ExplainabilityRow objects
        """
        rows = []

        for record in evaluation_records:
            try:
                row = self._convert_live_record(record, position_id, portfolio_id, symbol)
                if row:
                    rows.append(row)
            except Exception as e:
                logger.warning(f"Failed to convert live record: {e}")
                continue

        return rows

    def enrich_with_orders(self, rows: List[ExplainabilityRow]) -> List[ExplainabilityRow]:
        """
        Enrich explainability rows with Order and Trade entity data.

        Batch-fetches all referenced orders and their trades, then populates
        Group 6 (Order Status) and Group 7 (Execution Details) fields.

        Args:
            rows: List of ExplainabilityRow objects with order_id populated

        Returns:
            The same list with enriched fields (mutated in place)
        """
        if not self._orders_repo or not self._trades_repo:
            return rows

        # Collect unique order IDs
        order_ids = {r.order_id for r in rows if r.order_id}
        if not order_ids:
            return rows

        # Batch-fetch orders
        orders_by_id: Dict[str, Any] = {}
        for order_id in order_ids:
            try:
                order = self._orders_repo.get(order_id)
                if order:
                    orders_by_id[order_id] = order
            except Exception as e:
                logger.warning(f"Failed to fetch order {order_id}: {e}")

        # Batch-fetch trades for each order
        trades_by_order: Dict[str, List[Any]] = {}
        for order_id in orders_by_id:
            try:
                trades = self._trades_repo.list_for_order(order_id)
                if trades:
                    trades_by_order[order_id] = trades
            except Exception as e:
                logger.warning(f"Failed to fetch trades for order {order_id}: {e}")

        # Enrich each row
        for row in rows:
            if not row.order_id or row.order_id not in orders_by_id:
                continue

            order = orders_by_id[row.order_id]

            # Group 6: Order Status
            row.order_status = order.status
            row.broker_order_id = order.broker_order_id
            row.broker_status = order.broker_status

            # Group 7: Execution Details from order
            if order.avg_fill_price is not None:
                row.execution_price = order.avg_fill_price
            if order.filled_qty:
                row.execution_qty = order.filled_qty
            if row.execution_price and row.execution_qty:
                row.execution_value = row.execution_price * row.execution_qty
            if order.total_commission:
                row.commission = order.total_commission

            # Determine execution status
            if order.status == "filled":
                row.execution_status = "FILLED"
            elif order.status == "partial":
                row.execution_status = "PARTIAL"
            elif order.status in ("rejected", "cancelled"):
                row.execution_status = "NONE"
            elif order.filled_qty and order.filled_qty > 0:
                row.execution_status = "PARTIAL"

            # Enrich with individual trade details if available
            trades = trades_by_order.get(row.order_id, [])
            if trades:
                total_qty = sum(abs(t.qty) for t in trades)
                total_commission = sum(t.commission for t in trades)
                if total_qty > 0:
                    weighted_price = sum(abs(t.qty) * t.price for t in trades) / total_qty
                    row.execution_price = weighted_price
                    row.execution_qty = total_qty
                    row.execution_value = weighted_price * total_qty
                    row.commission = total_commission

        return rows

    def build_from_simulation(
        self,
        simulation_result: Dict[str, Any],
    ) -> List[ExplainabilityRow]:
        """
        Build explainability rows from simulation result.

        Args:
            simulation_result: Simulation result dict with time_series_data, trade_log, etc.

        Returns:
            List of ExplainabilityRow objects
        """
        time_series_data = simulation_result.get("time_series_data", [])
        if not time_series_data:
            logger.warning("No time_series_data found in simulation result")
            return []

        trade_log = simulation_result.get("trade_log", [])
        simulation_id = simulation_result.get("id") or simulation_result.get("simulation_id")
        ticker = simulation_result.get("ticker", "")

        # Build trade lookup by timestamp
        trades_by_timestamp = {}
        for trade in trade_log:
            ts = trade.get("timestamp", "")
            if ts not in trades_by_timestamp:
                trades_by_timestamp[ts] = []
            trades_by_timestamp[ts].append(trade)

        rows = []
        for ts_data in time_series_data:
            try:
                row = self._convert_simulation_record(
                    ts_data, trades_by_timestamp, simulation_id, ticker
                )
                if row:
                    rows.append(row)
            except Exception as e:
                logger.warning(f"Failed to convert simulation record: {e}")
                continue

        return rows

    def aggregate_to_daily(
        self,
        rows: List[ExplainabilityRow],
    ) -> List[ExplainabilityRow]:
        """
        Apply daily aggregation logic.

        Granularity Rule:
        - Group events by date
        - If NO actions on a day (only HOLD): show 1 row at start of day
        - If actions exist (BUY/SELL/SKIP): show all action rows, omit HOLD rows

        Args:
            rows: List of all explainability rows

        Returns:
            Aggregated list of rows
        """
        # Group by date
        rows_by_date: Dict[str, List[ExplainabilityRow]] = defaultdict(list)
        for row in rows:
            rows_by_date[row.date_str].append(row)

        aggregated = []
        action_types = {"BUY", "SELL", "SKIP"}

        for date_str in sorted(rows_by_date.keys()):
            day_rows = rows_by_date[date_str]

            # Check if any actions occurred
            action_rows = [r for r in day_rows if r.action in action_types]

            if action_rows:
                # Show all action rows (sorted by timestamp)
                action_rows.sort(key=lambda r: r.timestamp)
                aggregated.extend(action_rows)
            else:
                # No actions - show first row of the day only
                day_rows.sort(key=lambda r: r.timestamp)
                if day_rows:
                    aggregated.append(day_rows[0])

        return aggregated

    def filter_rows(
        self,
        rows: List[ExplainabilityRow],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        actions: Optional[List[str]] = None,
        order_statuses: Optional[List[str]] = None,
    ) -> List[ExplainabilityRow]:
        """
        Filter rows by date range, action types, and order status.

        Args:
            rows: List of rows to filter
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)
            actions: List of action types to include (e.g., ["BUY", "SELL"])
            order_statuses: List of order statuses to include (e.g., ["filled", "rejected"])

        Returns:
            Filtered list of rows
        """
        filtered = rows

        if start_date:
            filtered = [r for r in filtered if r.timestamp >= start_date]

        if end_date:
            filtered = [r for r in filtered if r.timestamp <= end_date]

        if actions:
            actions_upper = [a.upper() for a in actions]
            filtered = [r for r in filtered if r.action in actions_upper]

        if order_statuses:
            statuses_lower = [s.lower() for s in order_statuses]
            filtered = [
                r for r in filtered
                if r.order_status and r.order_status.lower() in statuses_lower
            ]

        return filtered

    def build_timeline(
        self,
        rows: List[ExplainabilityRow],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        actions: Optional[List[str]] = None,
        order_statuses: Optional[List[str]] = None,
        aggregation: str = "daily",
        offset: int = 0,
        limit: int = 500,
        position_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        simulation_run_id: Optional[str] = None,
        symbol: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> ExplainabilityTimeline:
        """
        Build complete explainability timeline with filtering, aggregation, and pagination.

        Args:
            rows: Raw explainability rows
            start_date: Start date filter
            end_date: End date filter
            actions: Action types to include
            order_statuses: Order statuses to include
            aggregation: "daily" or "all"
            offset: Number of rows to skip (for pagination)
            limit: Maximum rows to return
            position_id: Position ID for metadata
            portfolio_id: Portfolio ID for metadata
            simulation_run_id: Simulation ID for metadata
            symbol: Asset symbol for metadata
            mode: Mode (LIVE or SIMULATION)

        Returns:
            ExplainabilityTimeline response object
        """
        total_rows = len(rows)

        # Apply filters first
        filtered = self.filter_rows(rows, start_date, end_date, actions, order_statuses)

        # Apply aggregation
        if aggregation == "daily":
            filtered = self.aggregate_to_daily(filtered)

        filtered_count = len(filtered)

        # Sort by timestamp descending (newest first)
        filtered.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply pagination (offset + limit)
        if offset > 0:
            filtered = filtered[offset:]
        if limit and limit > 0:
            filtered = filtered[:limit]

        return ExplainabilityTimeline(
            rows=filtered,
            total_rows=total_rows,
            filtered_rows=filtered_count,
            offset=offset,
            limit=limit,
            position_id=position_id,
            portfolio_id=portfolio_id,
            simulation_run_id=simulation_run_id,
            symbol=symbol,
            mode=mode,
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
            actions_filter=actions,
            order_status_filter=order_statuses,
            aggregation=aggregation,
        )

    # ========== Private Conversion Methods ==========

    def _convert_live_record(
        self,
        record: Dict[str, Any],
        position_id: Optional[str],
        portfolio_id: Optional[str],
        symbol: Optional[str],
    ) -> Optional[ExplainabilityRow]:
        """Convert a live timeline record to ExplainabilityRow."""
        timestamp = record.get("timestamp") or record.get("evaluated_at")
        if not timestamp:
            return None

        if isinstance(timestamp, str):
            timestamp = self._parse_timestamp(timestamp)
        if not timestamp:
            return None

        # Get effective price
        price = (
            record.get("effective_price")
            or record.get("market_price_raw")
            or record.get("close_price")
            or 0.0
        )

        # Calculate position values
        qty = record.get("position_qty_before") or record.get("position_qty_after") or 0.0
        cash = record.get("position_cash_before") or record.get("position_cash_after") or 0.0
        stock_value = qty * price if qty and price else 0.0
        total_value = stock_value + cash
        stock_pct = (stock_value / total_value * 100) if total_value > 0 else None

        # Get action
        action = record.get("action") or "HOLD"
        if isinstance(action, str):
            action = action.upper()
        if action not in ("BUY", "SELL", "HOLD", "SKIP"):
            action = "HOLD"

        # Guardrail info
        guardrail_allowed = record.get("guardrail_allowed")
        if guardrail_allowed is None:
            guardrail_allowed = True
        elif isinstance(guardrail_allowed, str):
            guardrail_allowed = guardrail_allowed.upper() != "BLOCKED"

        # Position impact: before values
        qty_before = record.get("position_qty_before")
        cash_before = record.get("position_cash_before")
        stock_value_before = record.get("position_stock_value_before")
        total_value_before = record.get("position_total_value_before")
        if qty_before is not None and price and stock_value_before is None:
            stock_value_before = float(qty_before) * float(price)
        if cash_before is not None and stock_value_before is not None and total_value_before is None:
            total_value_before = float(cash_before) + float(stock_value_before)
        stock_pct_before = None
        if stock_value_before is not None and total_value_before and total_value_before > 0:
            stock_pct_before = float(stock_value_before) / float(total_value_before) * 100

        # Position impact: after values
        qty_after = record.get("position_qty_after")
        cash_after = record.get("position_cash_after")
        stock_value_after = None
        total_value_after = None
        if qty_after is not None and price:
            stock_value_after = float(qty_after) * float(price)
        if cash_after is not None and stock_value_after is not None:
            total_value_after = float(cash_after) + float(stock_value_after)
        stock_pct_after = None
        if stock_value_after is not None and total_value_after and total_value_after > 0:
            stock_pct_after = float(stock_value_after) / float(total_value_after) * 100

        # Trigger evaluation details
        trigger_detected = record.get("trigger_detected", False)
        trigger_direction = record.get("trigger_direction")
        trigger_up = record.get("trigger_up_threshold")
        trigger_down = record.get("trigger_down_threshold")

        # Anchor tracking
        anchor_reset = record.get("anchor_reset_occurred", False)
        anchor_old_value = record.get("anchor_price_old")
        anchor_reset_reason = record.get("anchor_reset_reason")

        # Dividend fields
        dividend_declared = record.get("dividend_declared", False)
        dividend_receivable = record.get("position_dividend_receivable_before")

        return ExplainabilityRow(
            timestamp=timestamp,
            date_str=timestamp.strftime("%Y-%m-%d"),
            trace_id=record.get("trace_id"),

            # Group 2: Market
            price=price,
            open_price=record.get("open_price"),
            high_price=record.get("high_price"),
            low_price=record.get("low_price"),
            close_price=record.get("close_price"),
            volume=record.get("volume"),

            # Group 3: Trigger Evaluation
            anchor_price=record.get("anchor_price"),
            delta_pct=record.get("pct_change_from_anchor"),
            trigger_up_threshold=trigger_up,
            trigger_down_threshold=trigger_down,
            trigger_fired=trigger_detected,
            trigger_direction=trigger_direction,
            trigger_reason=record.get("trigger_reason"),

            # Group 4: Guardrails
            min_stock_pct=record.get("guardrail_min_stock_pct"),
            max_stock_pct=record.get("guardrail_max_stock_pct"),
            current_stock_pct=stock_pct_before,
            guardrail_allowed=guardrail_allowed,
            guardrail_block_reason=record.get("guardrail_block_reason"),

            # Group 5: Action
            action=action,
            action_reason=record.get("action_reason") or record.get("trigger_reason"),
            intended_qty=record.get("proposed_qty"),
            intended_value=record.get("proposed_value"),

            # Group 6: Order Status (populated from record, enriched later)
            order_id=record.get("order_id"),

            # Group 7: Execution
            execution_price=record.get("execution_price"),
            execution_qty=record.get("execution_qty"),
            commission=record.get("execution_commission") or record.get("commission_value"),

            # Group 8: Position Impact
            qty_before=qty_before,
            qty_after=qty_after,
            cash_before=cash_before,
            cash_after=cash_after,
            stock_value_before=stock_value_before,
            stock_value_after=stock_value_after,
            total_value_before=total_value_before,
            total_value_after=total_value_after,
            stock_pct_before=stock_pct_before,
            stock_pct_after=stock_pct_after,

            # Group 9: Dividends
            dividend_declared=dividend_declared,

            # Group 10: Anchor Tracking
            anchor_reset=anchor_reset,
            anchor_old_value=anchor_old_value,
            anchor_reset_reason=anchor_reset_reason,

            # Legacy/Convenience
            qty=qty,
            stock_value=stock_value,
            cash=cash,
            total_value=total_value,
            stock_pct=stock_pct,

            # Metadata
            mode="LIVE",
            simulation_run_id=None,
            position_id=position_id or record.get("position_id"),
            portfolio_id=portfolio_id or record.get("portfolio_id"),
            symbol=symbol or record.get("symbol"),
            evaluation_id=record.get("id"),
        )

    def _convert_simulation_record(
        self,
        ts_data: Dict[str, Any],
        trades_by_timestamp: Dict[str, List[Dict[str, Any]]],
        simulation_id: Optional[str],
        ticker: str,
    ) -> Optional[ExplainabilityRow]:
        """Convert a simulation time series record to ExplainabilityRow."""
        timestamp_str = ts_data.get("timestamp", "")
        timestamp = self._parse_timestamp(timestamp_str)
        if not timestamp:
            return None

        # Get price
        price = ts_data.get("price", 0) or ts_data.get("close", 0)

        # Get OHLC
        open_price = ts_data.get("open")
        high_price = ts_data.get("high")
        low_price = ts_data.get("low")
        close_price = ts_data.get("close")

        # Position values
        qty = ts_data.get("shares", 0) or ts_data.get("qty", 0)
        cash = ts_data.get("cash", 0)
        stock_value = qty * price if qty and price else 0.0
        total_value = ts_data.get("total_value", stock_value + cash)
        stock_pct = (stock_value / total_value * 100) if total_value > 0 else None

        # Anchor
        anchor_price = ts_data.get("anchor_price", 0)
        delta_pct = None
        if anchor_price and anchor_price > 0 and price:
            delta_pct = ((price - anchor_price) / anchor_price) * 100

        # Guardrails
        min_stock_pct = self._normalize_guardrail_pct(ts_data.get("guardrail_min_stock_pct"), 20.0)
        max_stock_pct = self._normalize_guardrail_pct(ts_data.get("guardrail_max_stock_pct"), 60.0)

        # Check for trades at this timestamp
        trades_at_ts = trades_by_timestamp.get(timestamp_str, [])
        action = "HOLD"
        action_reason = "No trigger"
        execution_price = None
        execution_qty = None
        commission = None
        guardrail_allowed = True
        guardrail_block_reason = None

        # Determine action from trigger info
        triggered = ts_data.get("triggered", False)
        trigger_side = ts_data.get("side")
        executed = ts_data.get("executed", False)

        if triggered:
            if trigger_side and trigger_side.upper() == "BUY":
                action = "BUY" if executed else "SKIP"
            elif trigger_side and trigger_side.upper() == "SELL":
                action = "SELL" if executed else "SKIP"

            if not executed:
                guardrail_allowed = False
                guardrail_block_reason = ts_data.get("execution_error", "Guardrail blocked")
                action_reason = ts_data.get("reason", "Trigger blocked by guardrail")
            else:
                action_reason = f"Trigger {trigger_side}, executed"
        else:
            action_reason = ts_data.get("reason", "Inside band - no trigger")

        # Get execution details from trades
        if trades_at_ts:
            total_qty = sum(abs(t.get("qty", 0)) for t in trades_at_ts)
            total_commission = sum(t.get("commission", 0) for t in trades_at_ts)
            weighted_price = (
                sum(abs(t.get("qty", 0)) * t.get("price", 0) for t in trades_at_ts) / total_qty
                if total_qty > 0
                else 0
            )
            trade_side = trades_at_ts[0].get("side", "").upper()

            action = trade_side if trade_side in ("BUY", "SELL") else action
            execution_price = weighted_price if weighted_price > 0 else trades_at_ts[0].get("price")
            execution_qty = total_qty
            commission = total_commission
            action_reason = f"{trade_side} executed"
            guardrail_allowed = True

        return ExplainabilityRow(
            timestamp=timestamp,
            date_str=timestamp.strftime("%Y-%m-%d"),

            # Market
            price=price,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=ts_data.get("volume"),

            # Anchor
            anchor_price=anchor_price,
            delta_pct=delta_pct,

            # Position
            qty=qty,
            stock_value=stock_value,
            cash=cash,
            total_value=total_value,
            stock_pct=stock_pct,

            # Guardrails
            min_stock_pct=min_stock_pct,
            max_stock_pct=max_stock_pct,
            guardrail_allowed=guardrail_allowed,
            guardrail_block_reason=guardrail_block_reason,

            # Action
            action=action,
            action_reason=action_reason,

            # Execution
            execution_price=execution_price,
            execution_qty=execution_qty,
            commission=commission,

            # Metadata
            mode="SIMULATION",
            simulation_run_id=simulation_id,
            position_id=None,
            portfolio_id=None,
            symbol=ticker,
            evaluation_id=None,
        )

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime."""
        if not timestamp_str:
            return None

        try:
            # Normalize the timestamp string
            normalized = timestamp_str.replace("Z", "+00:00")

            # Handle space-separated format (e.g., "2026-02-04 15:38:09.330803+00:00")
            if " " in normalized and "T" not in normalized:
                normalized = normalized.replace(" ", "T", 1)

            # Try ISO format
            if "T" in normalized:
                return datetime.fromisoformat(normalized)

            # Try date-only format
            return datetime.strptime(normalized, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            return None

    @staticmethod
    def _normalize_guardrail_pct(value: Any, default: float) -> float:
        """Normalize guardrail percentage values (handle 0-1 vs 0-100 scale)."""
        if value is None:
            return default
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return default
        # If value is between 0 and 1, assume it's a ratio and convert to percentage
        if 0 <= numeric <= 1:
            return numeric * 100
        return numeric
