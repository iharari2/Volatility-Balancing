# =========================
# backend/application/services/trading_worker.py
# =========================
"""
Trading Worker - Background scheduler for automated trading cycles.

This worker runs independently of the GUI and executes trading cycles
on a schedule for all active positions.

Core principle: Trading must run even if no user is logged in and the GUI is down.
"""

from __future__ import annotations
import time
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging
import json
from pathlib import Path

from app.di import container

logger = logging.getLogger(__name__)

# Persist worker state in local logs directory
WORKER_STATE_FILE = Path("logs/trading_worker_state.json")


class TradingWorker:
    """
    Background worker that runs trading cycles on schedule.

    This is the "engine" layer - it runs independently of any GUI.
    """

    def __init__(
        self,
        interval_seconds: int = 60,
        enabled: bool = True,
    ):
        """
        Initialize trading worker.

        Args:
            interval_seconds: How often to run trading cycles (default: 60 seconds)
            enabled: Whether the worker is enabled (default: True)
        """
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the trading worker in a background thread."""
        with self._lock:
            if self._running:
                logger.warning("Trading worker is already running")
                return

            self._running = True
            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="TradingWorker",
            )
            self._thread.start()
            logger.info(
                f"✅ Trading worker started (interval: {self.interval_seconds}s, enabled: {self.enabled})"
            )

    def stop(self) -> None:
        """Stop the trading worker."""
        with self._lock:
            if not self._running:
                return

            self._running = False
            self._stop_event.set()

            if self._thread:
                self._thread.join(timeout=10)

            logger.info("🛑 Trading worker stopped")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the worker (without stopping the thread)."""
        with self._lock:
            self.enabled = enabled
            # Persist state to disk so it survives server restarts
            self._save_state()
            logger.info(f"Trading worker {'enabled' if enabled else 'disabled'} (state persisted)")

    def set_interval(self, interval_seconds: int) -> None:
        """Update the polling interval."""
        with self._lock:
            self.interval_seconds = max(1, interval_seconds)  # Minimum 1 second
            # Persist state to disk
            self._save_state()
            logger.info(
                f"Trading worker interval updated to {self.interval_seconds}s (state persisted)"
            )

    def _save_state(self) -> None:
        """Save worker state to disk for persistence across server restarts."""
        try:
            state = {
                "enabled": self.enabled,
                "interval_seconds": self.interval_seconds,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            WORKER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(WORKER_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Worker state saved to {WORKER_STATE_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save worker state: {e}")

    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        with self._lock:
            return self._running

    def _run_loop(self) -> None:
        """Main worker loop - runs trading cycles on schedule."""
        logger.info("🔄 Trading worker loop started")

        while not self._stop_event.is_set():
            try:
                if self.enabled:
                    self._run_cycle()

                # Wait for next interval (or until stop event)
                self._stop_event.wait(self.interval_seconds)

            except Exception as e:
                logger.error(f"⚠️  Error in trading worker loop: {e}", exc_info=True)
                # Continue running even if one cycle fails
                time.sleep(min(5, self.interval_seconds))  # Brief pause before retry

        logger.info("🛑 Trading worker loop stopped")

    def _run_cycle(self) -> None:
        """
        Execute one trading cycle for all active positions.

        This calls the LiveTradingOrchestrator which handles:
        - Fetching market data
        - Evaluating triggers
        - Checking guardrails
        - Submitting orders
        - Logging all events to audit trail
        """
        try:
            start_time = datetime.now(timezone.utc)
            logger.debug(f"🔄 Running trading cycle at {start_time.isoformat()}")

            # Get orchestrator from DI container
            orchestrator = container.live_trading_orchestrator

            # Run cycle for all active positions
            # Source is "worker" to distinguish from manual API calls
            orchestrator.run_cycle(source="worker")

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.debug(f"✅ Trading cycle completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"⚠️  Error running trading cycle: {e}", exc_info=True)


# Global worker instance
_trading_worker: Optional[TradingWorker] = None


def _load_worker_state() -> Dict[str, Any]:
    """Load worker state from disk if it exists."""
    try:
        if WORKER_STATE_FILE.exists():
            with open(WORKER_STATE_FILE, "r") as f:
                state = json.load(f)
                logger.info(
                    f"Loaded worker state from {WORKER_STATE_FILE}: enabled={state.get('enabled')}, interval={state.get('interval_seconds')}s"
                )
                return state
    except Exception as e:
        logger.warning(f"Failed to load worker state: {e}")
    return {}


def get_trading_worker() -> TradingWorker:
    """Get or create the global trading worker instance."""
    global _trading_worker
    if _trading_worker is None:
        # Try to load persisted state first
        persisted_state = _load_worker_state()

        # Use persisted state if available, otherwise fall back to environment variables
        import os

        interval = persisted_state.get("interval_seconds") or int(
            os.getenv("TRADING_WORKER_INTERVAL_SECONDS", "60")
        )
        enabled = persisted_state.get("enabled")
        enabled_env = os.getenv("TRADING_WORKER_ENABLED")
        if enabled_env is not None:
            enabled = enabled_env.lower() == "true"
        elif enabled is None:
            enabled = os.getenv("TRADING_WORKER_ENABLED", "true").lower() == "true"

        _trading_worker = TradingWorker(interval_seconds=interval, enabled=enabled)
        logger.info(f"Trading worker initialized: enabled={enabled}, interval={interval}s")
    return _trading_worker


def start_trading_worker() -> None:
    """Start the global trading worker (called on backend startup)."""
    worker = get_trading_worker()
    if not worker.is_running():
        worker.start()


def stop_trading_worker() -> None:
    """Stop the global trading worker (called on backend shutdown)."""
    global _trading_worker
    if _trading_worker and _trading_worker.is_running():
        _trading_worker.stop()
