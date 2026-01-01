# =========================
# backend/application/services/verbose_timeline_service.py
# =========================
"""
Verbose Timeline Service - Builds row-by-row timeline view for simulation and live trading.

Each row represents a single evaluation point (e.g. daily bar, or each trading cycle)
for a given portfolio + asset, showing all incremental changes per step in time.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class VerboseTimelineService:
    """Service for building verbose timeline views from simulation or live trading data."""

    def build_timeline_from_simulation(
        self, simulation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build verbose timeline from simulation result.

        Args:
            simulation_result: Simulation result dict with time_series_data, trade_log, etc.

        Returns:
            List of timeline rows, each representing one time step
        """
        time_series_data = simulation_result.get("time_series_data", [])
        if not time_series_data:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("No time_series_data found in simulation result")
            return []

        trade_log = simulation_result.get("trade_log", [])
        dividend_analysis = simulation_result.get("dividend_analysis", {})
        dividend_events = dividend_analysis.get("dividends", []) if dividend_analysis else []
        trigger_analysis = simulation_result.get("trigger_analysis", [])

        # Try to get price_data for OHLC if not in time_series_data
        price_data_list = simulation_result.get("price_data", [])
        price_data_by_timestamp = {}
        for price_point in price_data_list:
            ts = price_point.get("timestamp") or price_point.get("date")
            if ts:
                price_data_by_timestamp[ts] = price_point

        # Build trade lookup by timestamp
        trades_by_timestamp = {}
        for trade in trade_log:
            ts = trade.get("timestamp", "")
            if ts not in trades_by_timestamp:
                trades_by_timestamp[ts] = []
            trades_by_timestamp[ts].append(trade)

        # Build dividend lookup by date
        dividends_by_date = {}
        for div in dividend_events:
            ex_date = div.get("ex_date", "")
            if ex_date not in dividends_by_date:
                dividends_by_date[ex_date] = []
            dividends_by_date[ex_date].append(div)

        # Build trigger analysis lookup
        trigger_by_timestamp = {}
        for trigger in trigger_analysis:
            ts = trigger.get("timestamp", "")
            if ts:
                trigger_by_timestamp[ts] = trigger

        # Get baseline (first row)
        baseline_stock_value = None
        baseline_total_value = None
        if time_series_data:
            first_row = time_series_data[0]
            baseline_stock_value = first_row.get("asset_value", 0)
            baseline_total_value = first_row.get("total_value", 0)

        # Build timeline rows
        timeline_rows = []
        prev_close = None
        prev_total_value = None

        for idx, ts_data in enumerate(time_series_data):
            timestamp_str = ts_data.get("timestamp", "")
            date_str = ts_data.get("date", "")
            current_time = self._parse_timestamp(timestamp_str)

            # Get OHLCV data
            # Check if OHLC is in the time series data directly
            price = ts_data.get("price", 0)

            # Try to get OHLC from time_series_data first
            open_price = ts_data.get("open")
            high_price = ts_data.get("high")
            low_price = ts_data.get("low")
            close_price = ts_data.get("close")

            # If not in time_series_data, try price_data lookup
            if open_price is None and timestamp_str in price_data_by_timestamp:
                price_point = price_data_by_timestamp[timestamp_str]
                open_price = price_point.get("open")
                high_price = price_point.get("high")
                low_price = price_point.get("low")
                close_price = price_point.get("close")

            # Fallback to price if still not available
            open_price = open_price if open_price is not None else price
            high_price = high_price if high_price is not None else price
            low_price = low_price if low_price is not None else price
            close_price = close_price if close_price is not None else price

            volume = ts_data.get("volume", 0)

            # Use close as the primary price
            current_close = close_price if close_price else price

            # Anchor price
            anchor_price = ts_data.get("anchor_price", 0)

            # Position and portfolio values
            quantity = ts_data.get("shares", 0) or ts_data.get("qty", 0)
            position_value = quantity * current_close
            cash = ts_data.get("cash", 0)
            total_portfolio_value = ts_data.get("total_value", cash + position_value)

            # Price change metrics
            pct_change_from_prev = None
            if prev_close is not None and prev_close > 0:
                pct_change_from_prev = ((current_close - prev_close) / prev_close) * 100

            pct_change_from_anchor = None
            if anchor_price and anchor_price > 0:
                pct_change_from_anchor = ((current_close - anchor_price) / anchor_price) * 100

            # Portfolio value changes
            delta_total_value = None
            pct_delta_total_value = None
            if prev_total_value is not None:
                delta_total_value = total_portfolio_value - prev_total_value
                if prev_total_value > 0:
                    pct_delta_total_value = (delta_total_value / prev_total_value) * 100

            # Baseline comparisons
            pct_stock_change_from_baseline = None
            if baseline_stock_value and baseline_stock_value > 0:
                pct_stock_change_from_baseline = (
                    (position_value - baseline_stock_value) / baseline_stock_value
                ) * 100

            pct_portfolio_change_from_baseline = None
            if baseline_total_value and baseline_total_value > 0:
                pct_portfolio_change_from_baseline = (
                    (total_portfolio_value - baseline_total_value) / baseline_total_value
                ) * 100

            # Trigger and guardrail state
            trigger_threshold_up = ts_data.get("trigger_threshold_pct", 0)
            trigger_threshold_down = -abs(trigger_threshold_up)  # Negative threshold

            # Get trigger info from time series or trigger analysis
            triggered = ts_data.get("triggered", False)
            trigger_side = ts_data.get("side")
            trigger_reason = ts_data.get("reason", "INSIDE_BAND")

            # Map trigger side to signal
            trigger_signal = "NONE"
            if triggered:
                if trigger_side and trigger_side.upper() in ["BUY", "buy"]:
                    trigger_signal = "BUY"
                elif trigger_side and trigger_side.upper() in ["SELL", "sell"]:
                    trigger_signal = "SELL"

            # Normalize trigger reason
            if not triggered:
                trigger_reason = "INSIDE_BAND"
            elif trigger_reason:
                trigger_reason = trigger_reason.upper().replace(" ", "_")
            else:
                trigger_reason = "TRIGGERED"

            # Guardrail config
            # Try to extract from time_series_data or use defaults
            # These should ideally come from the position config at that time
            guardrail_min_stock_pct = ts_data.get("guardrail_min_stock_pct", 20.0)
            guardrail_max_stock_pct = ts_data.get("guardrail_max_stock_pct", 60.0)
            guardrail_max_trade_pct_of_position = ts_data.get(
                "guardrail_max_trade_pct_of_position", 10.0
            )

            # Guardrail decision
            guardrail_allowed = "ALLOWED"
            guardrail_reason = "WITHIN_LIMITS"

            # Check if trade was executed (indicates guardrail passed)
            executed = ts_data.get("executed", False)
            if triggered and not executed:
                guardrail_allowed = "BLOCKED"
                guardrail_reason = ts_data.get("execution_error", "GUARDRAIL_BLOCKED")

            # Action and trade values
            action = "NO_TRADE"
            action_reason = "No trigger"

            # Check for trades at this timestamp
            trades_at_ts = trades_by_timestamp.get(timestamp_str, [])
            trade_side = None
            trade_quantity = 0
            trade_price = 0
            trade_notional = 0
            trade_commission = 0
            trade_commission_rate_effective = 0

            if trades_at_ts:
                # Aggregate trades at this timestamp
                total_qty = sum(abs(t.get("qty", 0)) for t in trades_at_ts)
                total_commission = sum(t.get("commission", 0) for t in trades_at_ts)
                weighted_price = (
                    sum(abs(t.get("qty", 0)) * t.get("price", 0) for t in trades_at_ts) / total_qty
                    if total_qty > 0
                    else 0
                )

                trade_side = trades_at_ts[0].get("side", "").upper()
                trade_quantity = total_qty
                trade_price = (
                    weighted_price if weighted_price > 0 else trades_at_ts[0].get("price", 0)
                )
                trade_notional = trade_quantity * trade_price
                trade_commission = total_commission
                trade_commission_rate_effective = (
                    (trade_commission / trade_notional * 100) if trade_notional > 0 else 0
                )

                action = trade_side
                action_reason = f"Trigger {trade_side}, guardrail allowed, executed"

            # Check for dividend events
            dividend_percent = 0
            dividend_value = 0
            dividend_cash_this_line = 0

            # Check if dividend occurred on this date
            div_events = dividends_by_date.get(date_str, [])
            if div_events:
                # Use the first dividend event for this date
                div = div_events[0]
                dps = div.get("dps", 0)
                withholding_rate = div.get("withholding_tax_rate", 0) / 100

                dividend_percent = (dps / current_close * 100) if current_close > 0 else 0
                dividend_gross = quantity * dps
                dividend_net = dividend_gross * (1 - withholding_rate)
                dividend_value = dividend_net
                dividend_cash_this_line = dividend_net

                if action == "NO_TRADE":
                    action = "DIVIDEND"
                    action_reason = "Dividend credited"
                else:
                    action = "MULTI_ACTION"
                    action_reason = f"{action_reason}, dividend credited"

            # Also check time_series_data for dividend info
            if ts_data.get("dividend_event", False):
                dividend_dps = ts_data.get("dividend_dps", 0)
                dividend_net = ts_data.get("dividend_net", 0)
                if dividend_dps > 0:
                    dividend_percent = (
                        (dividend_dps / current_close * 100) if current_close > 0 else 0
                    )
                if dividend_net > 0:
                    dividend_value = dividend_net
                    dividend_cash_this_line = dividend_net

            # Build the row
            row = {
                "DateTime": timestamp_str,
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": current_close,
                "Volume": volume,
                "AnchorPrice": anchor_price,
                "DividendPercent": dividend_percent,
                "DividendValue": dividend_value,
                "PctChangeFromPrev": pct_change_from_prev,
                "PctChangeFromAnchor": pct_change_from_anchor,
                "Quantity": quantity,
                "PositionValue": position_value,
                "Cash": cash,
                "TotalPortfolioValue": total_portfolio_value,
                "DeltaTotalValue": delta_total_value,
                "PctDeltaTotalValue": pct_delta_total_value,
                "PctStockChangeFromBaseline": pct_stock_change_from_baseline,
                "PctPortfolioChangeFromBaseline": pct_portfolio_change_from_baseline,
                "TriggerThresholdUp": trigger_threshold_up,
                "TriggerThresholdDown": trigger_threshold_down,
                "TriggerSignal": trigger_signal,
                "TriggerReason": trigger_reason,
                "GuardrailMinStockPct": guardrail_min_stock_pct,
                "GuardrailMaxStockPct": guardrail_max_stock_pct,
                "GuardrailMaxTradePctOfPosition": guardrail_max_trade_pct_of_position,
                "GuardrailAllowed": guardrail_allowed,
                "GuardrailReason": guardrail_reason,
                "Action": action,
                "ActionReason": action_reason,
                "TradeSide": trade_side,
                "TradeQuantity": trade_quantity,
                "TradePrice": trade_price,
                "TradeNotional": trade_notional,
                "TradeCommission": trade_commission,
                "TradeCommissionRateEffective": trade_commission_rate_effective,
                "DividendCashThisLine": dividend_cash_this_line,
            }

            timeline_rows.append(row)

            # Update previous values
            prev_close = current_close
            prev_total_value = total_portfolio_value

        return timeline_rows

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime."""
        if not timestamp_str:
            return None

        try:
            # Try ISO format
            if "T" in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Try date format
            return datetime.strptime(timestamp_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            return None
