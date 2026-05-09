# =========================
# backend/application/services/continuous_trading_service.py
# =========================
"""
Continuous Trading Service for 24/7 automated virtual trading.

This service monitors positions at regular intervals, evaluates for triggers,
and automatically submits and fills orders in virtual trading mode.
"""

from __future__ import annotations
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Callable
from dataclasses import dataclass

from app.di import container
from application.use_cases.evaluate_position_uc import EvaluatePositionUC
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.dto.orders import CreateOrderRequest, FillOrderRequest
from domain.errors import GuardrailBreach


@dataclass
class TradingStatus:
    """Status of continuous trading for a position."""

    position_id: str
    is_running: bool = False
    is_paused: bool = False
    start_time: Optional[datetime] = None
    last_check: Optional[datetime] = None
    total_checks: int = 0
    total_trades: int = 0
    total_errors: int = 0
    last_error: Optional[str] = None


class ContinuousTradingService:
    """Service for continuous 24/7 automated trading."""

    def __init__(self):
        self._active_positions: Dict[str, TradingStatus] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_flags: Dict[str, threading.Event] = {}
        self._polling_interval: int = 300  # 5 minutes in seconds
        self._lock = threading.Lock()

    def start_trading(
        self,
        position_id: str,
        polling_interval_seconds: int = 300,
        callback: Optional[Callable[[str, Dict], None]] = None,
    ) -> bool:
        """Start continuous trading for a position.

        Args:
            position_id: ID of position to monitor
            polling_interval_seconds: How often to check (default 300 = 5 minutes)
            callback: Optional callback function for status updates

        Returns:
            True if started successfully, False if already running
        """
        with self._lock:
            if position_id in self._active_positions:
                status = self._active_positions[position_id]
                if status.is_running and not status.is_paused:
                    return False  # Already running
                elif status.is_paused:
                    # Resume
                    status.is_paused = False
                    return True

            # Create new status
            status = TradingStatus(
                position_id=position_id, is_running=True, start_time=datetime.now(timezone.utc)
            )
            self._active_positions[position_id] = status

            # Create stop event
            stop_event = threading.Event()
            self._stop_flags[position_id] = stop_event

            # Start monitoring thread
            thread = threading.Thread(
                target=self._monitor_position,
                args=(position_id, polling_interval_seconds, stop_event, callback),
                daemon=True,
            )
            thread.start()
            self._threads[position_id] = thread

            print(f"✅ Started continuous trading for position {position_id}")
            return True

    def stop_trading(self, position_id: str) -> bool:
        """Stop continuous trading for a position."""
        with self._lock:
            if position_id not in self._active_positions:
                return False

            # Signal stop
            if position_id in self._stop_flags:
                self._stop_flags[position_id].set()

            # Update status
            status = self._active_positions[position_id]
            status.is_running = False
            status.is_paused = False

            # Wait for thread to finish (with timeout)
            if position_id in self._threads:
                thread = self._threads[position_id]
                thread.join(timeout=10)
                del self._threads[position_id]

            if position_id in self._stop_flags:
                del self._stop_flags[position_id]

            print(f"🛑 Stopped continuous trading for position {position_id}")
            return True

    def pause_trading(self, position_id: str) -> bool:
        """Pause continuous trading (can be resumed)."""
        with self._lock:
            if position_id not in self._active_positions:
                return False
            status = self._active_positions[position_id]
            if not status.is_running:
                return False
            status.is_paused = True
            print(f"⏸️  Paused continuous trading for position {position_id}")
            return True

    def resume_trading(self, position_id: str) -> bool:
        """Resume paused trading."""
        with self._lock:
            if position_id not in self._active_positions:
                return False
            status = self._active_positions[position_id]
            if not status.is_paused:
                return False
            status.is_paused = False
            print(f"▶️  Resumed continuous trading for position {position_id}")
            return True

    def get_status(self, position_id: str) -> Optional[TradingStatus]:
        """Get trading status for a position."""
        with self._lock:
            return self._active_positions.get(position_id)

    def list_active(self) -> Dict[str, TradingStatus]:
        """List all actively trading positions."""
        with self._lock:
            return {
                pos_id: status
                for pos_id, status in self._active_positions.items()
                if status.is_running
            }

    def _monitor_position(
        self,
        position_id: str,
        interval_seconds: int,
        stop_event: threading.Event,
        callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        """Monitor a position in a background thread."""
        eval_uc = EvaluatePositionUC(
            positions=container.positions,
            events=container.events,
            market_data=container.market_data,
            clock=container.clock,
            trigger_config_provider=container.trigger_config_provider,
            guardrail_config_provider=container.guardrail_config_provider,
            order_policy_config_provider=container.order_policy_config_provider,
            config_repo=container.config,
            portfolio_repo=container.portfolio_repo,
            evaluation_timeline_repo=container.evaluation_timeline,
            orders_repo=container.orders,
        )

        submit_uc = SubmitOrderUC(
            positions=container.positions,
            orders=container.orders,
            events=container.events,
            idempotency=container.idempotency,
            config_repo=container.config,
            clock=container.clock,
        )

        execute_uc = ExecuteOrderUC(
            positions=container.positions,
            orders=container.orders,
            trades=container.trades,
            events=container.events,
            clock=container.clock,
            guardrail_config_provider=container.guardrail_config_provider,
            order_policy_config_provider=container.order_policy_config_provider,
            evaluation_timeline_repo=container.evaluation_timeline,
        )

        print(
            f"🔄 Starting monitoring loop for position {position_id} (interval: {interval_seconds}s)"
        )

        while not stop_event.is_set():
            try:
                # Check if paused
                with self._lock:
                    status = self._active_positions.get(position_id)
                    if not status or status.is_paused:
                        time.sleep(1)  # Short sleep when paused
                        continue

                # Update last check time
                status.last_check = datetime.now(timezone.utc)
                status.total_checks += 1

                # Get position - search across portfolios to find position by ID
                # NOTE: This is a legacy approach. In production, position_id should include
                # tenant_id and portfolio_id context, or the service should receive them as parameters.
                position = None
                tenant_id = "default"  # Default tenant for legacy support
                portfolio_id = None
                portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
                for portfolio in portfolios:
                    pos = container.positions.get(
                        tenant_id=tenant_id,
                        portfolio_id=portfolio.id,
                        position_id=position_id,
                    )
                    if pos:
                        position = pos
                        portfolio_id = portfolio.id
                        break

                if not position:
                    print(f"⚠️  Position {position_id} not found, stopping monitoring")
                    break

                # Evaluate position (fetches market data + writes timeline row)
                try:
                    evaluation = eval_uc.evaluate_with_market_data(
                        tenant_id, portfolio_id, position_id, source="live/continuous"
                    )

                    current_price = evaluation.get("current_price")
                    if current_price is None:
                        print(
                            f"⚠️  Could not fetch price for {position.asset_symbol}, skipping check"
                        )
                        status.total_errors += 1
                        status.last_error = "Market data unavailable"
                        time.sleep(interval_seconds)
                        continue

                    print(f"🔍 Evaluating position {position_id} at price ${current_price:.2f}")

                    trigger_detected = evaluation.get("trigger_detected", False)
                    order_proposal = evaluation.get("order_proposal")

                    print(f"   Trigger detected: {trigger_detected}")
                    if order_proposal:
                        print(
                            f"   Order proposal: {order_proposal.get('side')} {order_proposal.get('trimmed_qty', 0):.4f}"
                        )
                        validation = order_proposal.get("validation", {})
                        print(f"   Validation valid: {validation.get('valid', False)}")
                        if validation.get("rejections"):
                            print(f"   Rejections: {validation.get('rejections')}")

                    # Log evaluation event
                    if callback:
                        callback(
                            position_id,
                            {
                                "type": "evaluation",
                                "price": current_price,
                                "trigger_detected": trigger_detected,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )

                    # If trigger detected and order is valid, submit and fill
                    if trigger_detected and order_proposal:
                        validation = order_proposal.get("validation", {})
                        is_valid = validation.get("valid", False)

                        print(f"   Attempting to execute trade: valid={is_valid}")

                        if is_valid:
                            try:
                                print("   ✅ Order validation passed, proceeding with execution")
                                # Submit order
                                trimmed_qty = abs(order_proposal["trimmed_qty"])
                                print(
                                    f"   Submitting order: {order_proposal['side']} {trimmed_qty:.4f} @ ${current_price:.2f}"
                                )

                                order_request = CreateOrderRequest(
                                    side=order_proposal["side"],
                                    qty=trimmed_qty,
                                    price=current_price,
                                )

                                idempotency_key = f"auto_{position_id}_{int(time.time())}"
                                submit_response = submit_uc.execute(
                                    tenant_id,
                                    portfolio_id,
                                    position_id,
                                    order_request,
                                    idempotency_key,
                                )

                                print(
                                    f"   Order submitted: accepted={submit_response.accepted}, order_id={submit_response.order_id}"
                                )

                                if submit_response.accepted:
                                    # Auto-fill order immediately (virtual trading)
                                    fill_qty = abs(order_proposal["trimmed_qty"])
                                    fill_commission = order_proposal.get("commission", 0.0)

                                    print(
                                        f"   Filling order: qty={fill_qty:.4f}, price=${current_price:.2f}, commission=${fill_commission:.4f}"
                                    )

                                    fill_request = FillOrderRequest(
                                        qty=fill_qty,
                                        price=current_price,
                                        commission=fill_commission,
                                    )

                                    fill_response = execute_uc.execute(
                                        submit_response.order_id, fill_request
                                    )

                                    print(
                                        f"   Fill response: status={fill_response.status}, filled_qty={fill_response.filled_qty}"
                                    )

                                    if fill_response.status == "filled":
                                        status.total_trades += 1
                                        print(
                                            f"✅ Auto-trade executed: {order_proposal['side']} {order_proposal['trimmed_qty']:.4f} @ ${current_price:.2f}"
                                        )

                                        if callback:
                                            callback(
                                                position_id,
                                                {
                                                    "type": "trade_executed",
                                                    "side": order_proposal["side"],
                                                    "qty": order_proposal["trimmed_qty"],
                                                    "price": current_price,
                                                    "order_id": submit_response.order_id,
                                                    "trade_id": fill_response.trade_id,
                                                    "timestamp": datetime.now(
                                                        timezone.utc
                                                    ).isoformat(),
                                                },
                                            )
                                    else:
                                        print(
                                            f"   ⚠️  Order fill failed: status={fill_response.status}"
                                        )
                                        status.total_errors += 1
                                        status.last_error = f"Fill failed: {fill_response.status}"
                                else:
                                    print("   ⚠️  Order submission rejected")
                                    status.total_errors += 1
                                    status.last_error = "Order submission rejected"

                            except GuardrailBreach as e:
                                print(f"⚠️  Guardrail breach prevented trade: {e}")
                                status.total_errors += 1
                                status.last_error = f"Guardrail: {str(e)}"

                                if callback:
                                    callback(
                                        position_id,
                                        {
                                            "type": "guardrail_breach",
                                            "error": str(e),
                                            "timestamp": datetime.now(timezone.utc).isoformat(),
                                        },
                                    )

                            except Exception as e:
                                print(f"⚠️  Error executing trade: {e}")
                                import traceback

                                traceback.print_exc()
                                status.total_errors += 1
                                status.last_error = str(e)

                                if callback:
                                    callback(
                                        position_id,
                                        {
                                            "type": "trade_error",
                                            "error": str(e),
                                            "timestamp": datetime.now(timezone.utc).isoformat(),
                                        },
                                    )
                        else:
                            # Order proposal exists but validation failed
                            rejections = validation.get("rejections", [])
                            print(f"   ❌ Order validation failed: {rejections}")
                            status.total_errors += 1
                            status.last_error = f"Validation failed: {', '.join(rejections)}"

                            if callback:
                                callback(
                                    position_id,
                                    {
                                        "type": "validation_failed",
                                        "rejections": rejections,
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                    },
                                )
                    elif trigger_detected and not order_proposal:
                        print("   ⚠️  Trigger detected but no order proposal generated")
                        status.total_errors += 1
                        status.last_error = "Trigger detected but no order proposal"

                except Exception as e:
                    print(f"⚠️  Error evaluating position: {e}")
                    status.total_errors += 1
                    status.last_error = str(e)

            except Exception as e:
                print(f"⚠️  Unexpected error in monitoring loop: {e}")
                import traceback

                traceback.print_exc()
                status.total_errors += 1
                status.last_error = str(e)

            # Wait for next interval (or until stop event)
            stop_event.wait(interval_seconds)

        # Cleanup
        with self._lock:
            if position_id in self._active_positions:
                self._active_positions[position_id].is_running = False

        print(f"🛑 Monitoring stopped for position {position_id}")


# Global service instance
_continuous_trading_service = None


def get_continuous_trading_service() -> ContinuousTradingService:
    """Get or create the global continuous trading service instance."""
    global _continuous_trading_service
    if _continuous_trading_service is None:
        _continuous_trading_service = ContinuousTradingService()
    return _continuous_trading_service
