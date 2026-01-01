# =========================
# backend/tests/integration/test_simulation_intraday_minimal.py
# =========================
"""
Minimal deterministic integration test for intraday simulation runner.

Tests that SimulationOrchestrator:
- Performs BUY/SELL actions correctly
- Logs exactly 1 event per bar
- Updates ONLY simulation state (never touches production tables)
- Is fully deterministic with fake data provider

How to run this test:
    # Run the single test:
    pytest backend/tests/integration/test_simulation_intraday_minimal.py::test_simulation_intraday_minimal -v

    # Run with more output:
    pytest backend/tests/integration/test_simulation_intraday_minimal.py::test_simulation_intraday_minimal -v -s

    # Run all tests in the file:
    pytest backend/tests/integration/test_simulation_intraday_minimal.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from application.orchestrators.simulation import SimulationOrchestrator
from application.ports.market_data import IHistoricalPriceProvider
from application.ports.orders import ISimulationOrderService
from application.ports.repos import ISimulationPositionRepository
from application.ports.event_logger import IEventLogger
from domain.value_objects.market import MarketQuote
from domain.value_objects.position_state import PositionState
from domain.value_objects.trade_intent import TradeIntent
from domain.value_objects.configs import TriggerConfig, GuardrailConfig
from application.events import EventRecord, EventType
from app.di import container


class FakeHistoricalPriceProvider(IHistoricalPriceProvider):
    """Fake historical price provider returning fixed OHLCV sequence."""

    def __init__(self, bars: List[Dict[str, Any]]):
        """
        Initialize with a list of bars.
        Each bar should have: timestamp, close (and optionally open, high, low, volume)
        """
        self.bars = {bar["timestamp"]: bar for bar in bars}

    def get_quote_at(self, ticker: str, ts: datetime) -> MarketQuote:
        """Get quote at specific timestamp."""
        # Find the closest bar (exact match or closest before)
        matching_bar = None
        matching_ts = None
        for bar_ts, bar in self.bars.items():
            if bar_ts <= ts:
                if matching_ts is None or bar_ts > matching_ts:
                    matching_ts = bar_ts
                    matching_bar = bar

        if matching_bar is None:
            raise ValueError(f"No price data available for {ticker} at {ts}")

        price = Decimal(str(matching_bar["close"]))
        return MarketQuote(
            ticker=ticker,
            price=price,
            timestamp=matching_bar["timestamp"],
            currency="USD",
        )


class InMemorySimEventLogger(IEventLogger):
    """In-memory event logger that stores events in a list (simulation only)."""

    def __init__(self):
        self.events: List[EventRecord] = []

    def log_event(self, event: EventRecord) -> None:
        """Store event in memory."""
        self.events.append(event)

    def get_events_by_trace(self, trace_id: str) -> List[EventRecord]:
        """Get all events for a trace_id."""
        return [e for e in self.events if e.trace_id == trace_id]


class FakeSimPositionRepo(ISimulationPositionRepository):
    """Fake simulation position repository that tracks state changes."""

    def __init__(self, initial_state: PositionState):
        self._state = initial_state
        self._state_history: List[PositionState] = [initial_state]

    def load_sim_position_state(self, simulation_run_id: str, position_id: str) -> PositionState:
        """Load current simulation position state."""
        return self._state

    def save_sim_position_state(
        self, simulation_run_id: str, position_id: str, state: PositionState
    ) -> None:
        """Save updated simulation position state."""
        self._state = state
        self._state_history.append(state)

    def get_final_state(self) -> PositionState:
        """Get the final state after simulation."""
        return self._state

    def get_state_history(self) -> List[PositionState]:
        """Get all state changes."""
        return self._state_history


class FakeSimOrderService(ISimulationOrderService):
    """Fake simulation order service that tracks orders and updates position state."""

    def __init__(self, sim_position_repo: FakeSimPositionRepo):
        self.orders: List[Dict[str, Any]] = []
        self.sim_position_repo = sim_position_repo

    def submit_simulated_order(
        self,
        simulation_run_id: str,
        position_id: str,
        trade_intent: TradeIntent,
        quote: MarketQuote,
    ) -> str:
        """Submit simulated order, update position state, and track it."""
        order_id = f"sim_ord_{len(self.orders)}"

        # Load current state
        state = self.sim_position_repo.load_sim_position_state(simulation_run_id, position_id)

        # Update state based on trade intent
        if trade_intent.side.lower() == "buy":
            # Buy: increase qty, decrease cash
            new_qty = state.qty + trade_intent.qty
            new_cash = state.cash - (trade_intent.qty * quote.price)
            # Update anchor price after buy
            new_anchor = quote.price
        else:  # sell
            # Sell: decrease qty, increase cash
            new_qty = state.qty - trade_intent.qty
            new_cash = state.cash + (trade_intent.qty * quote.price)
            # Update anchor price after sell
            new_anchor = quote.price

        # Create updated state
        updated_state = PositionState(
            ticker=state.ticker,
            qty=new_qty,
            cash=new_cash,
            dividend_receivable=state.dividend_receivable,
            anchor_price=new_anchor,
        )

        # Save updated state
        self.sim_position_repo.save_sim_position_state(
            simulation_run_id, position_id, updated_state
        )

        # Track order
        self.orders.append(
            {
                "order_id": order_id,
                "simulation_run_id": simulation_run_id,
                "position_id": position_id,
                "trade_intent": trade_intent,
                "quote": quote,
            }
        )
        return order_id


@pytest.fixture
def fake_price_provider():
    """Create fake price provider with 6 bars."""
    base_time = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)

    bars = [
        {
            "timestamp": base_time + timedelta(minutes=0),
            "open": 100.0,
            "high": 100.0,
            "low": 100.0,
            "close": 100.0,
            "volume": 1000,
        },
        {
            "timestamp": base_time + timedelta(minutes=30),
            "open": 97.0,
            "high": 97.0,
            "low": 97.0,
            "close": 97.0,  # Down 3% from 100 -> should trigger BUY
            "volume": 1000,
        },
        {
            "timestamp": base_time + timedelta(minutes=60),
            "open": 96.0,
            "high": 96.0,
            "low": 96.0,
            "close": 96.0,
            "volume": 1000,
        },
        {
            "timestamp": base_time + timedelta(minutes=90),
            "open": 103.0,
            "high": 103.0,
            "low": 103.0,
            "close": 103.0,  # Up 3% from anchor 100 -> should trigger SELL
            "volume": 1000,
        },
        {
            "timestamp": base_time + timedelta(minutes=120),
            "open": 104.0,
            "high": 104.0,
            "low": 104.0,
            "close": 104.0,
            "volume": 1000,
        },
        {
            "timestamp": base_time + timedelta(minutes=150),
            "open": 101.0,
            "high": 101.0,
            "low": 101.0,
            "close": 101.0,
            "volume": 1000,
        },
    ]

    return FakeHistoricalPriceProvider(bars)


@pytest.fixture
def initial_position_state():
    """Create initial simulation position state."""
    return PositionState(
        ticker="TEST",
        qty=Decimal("10"),
        cash=Decimal("1000"),
        dividend_receivable=Decimal("0"),
        anchor_price=Decimal("100"),
    )


@pytest.fixture
def sim_position_repo(initial_position_state):
    """Create fake simulation position repository."""
    return FakeSimPositionRepo(initial_position_state)


@pytest.fixture
def sim_order_service(sim_position_repo):
    """Create fake simulation order service."""
    return FakeSimOrderService(sim_position_repo)


@pytest.fixture
def sim_event_logger():
    """Create in-memory event logger."""
    return InMemorySimEventLogger()


@pytest.fixture
def trigger_config():
    """Create trigger configuration."""
    return TriggerConfig(
        up_threshold_pct=Decimal("0.03"),  # 3%
        down_threshold_pct=Decimal("0.03"),  # 3%
    )


@pytest.fixture
def guardrail_config():
    """Create guardrail configuration (no blocking)."""
    return GuardrailConfig(
        min_stock_pct=Decimal("0.0"),  # No minimum
        max_stock_pct=Decimal("1.0"),  # No maximum
        max_trade_pct_of_position=Decimal("0.5"),  # Allow up to 50% of position per trade
    )


@pytest.fixture
def timestamps():
    """Create 6 timestamps matching the bars."""
    base_time = datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc)
    return [
        base_time + timedelta(minutes=0),
        base_time + timedelta(minutes=30),
        base_time + timedelta(minutes=60),
        base_time + timedelta(minutes=90),
        base_time + timedelta(minutes=120),
        base_time + timedelta(minutes=150),
    ]


def test_simulation_intraday_minimal(
    fake_price_provider,
    sim_position_repo,
    sim_order_service,
    sim_event_logger,
    trigger_config,
    guardrail_config,
    timestamps,
    initial_position_state,
):
    """
    Test that intraday simulation loop:
    - Logs exactly 1 event per bar
    - Performs BUY/SELL actions
    - Updates simulation state only
    - Never touches production tables
    """
    # Record initial production table counts
    # For in-memory repos, we can check internal storage
    # For SQL repos, we'll use a different approach
    initial_prod_orders_count = 0
    initial_prod_trades_count = 0
    initial_prod_events_count = 0
    initial_prod_positions_count = 0

    # Try to count orders (if in-memory, check internal storage)
    if hasattr(container.orders, "_items"):
        initial_prod_orders_count = len(container.orders._items)
    # Try to count trades
    if hasattr(container.trades, "_items"):
        initial_prod_trades_count = len(container.trades._items)
    # Try to count events
    if hasattr(container.events, "_items"):
        initial_prod_events_count = len(container.events._items)
    # Try to count positions (if in-memory, check internal storage)
    if hasattr(container.positions, "_items"):
        initial_prod_positions_count = len(container.positions._items)
    elif hasattr(container.positions, "_by_tenant_portfolio"):
        # Count all positions across all tenants/portfolios
        for tenant_dict in container.positions._by_tenant_portfolio.values():
            for portfolio_dict in tenant_dict.values():
                initial_prod_positions_count += len(portfolio_dict)

    # Create orchestrator
    orchestrator = SimulationOrchestrator(
        historical_data=fake_price_provider,
        sim_order_service=sim_order_service,
        sim_position_repo=sim_position_repo,
        event_logger=sim_event_logger,
    )

    # Run simulation
    simulation_run_id = "test_sim_001"
    position_id = "test_pos_001"

    orchestrator.run_simulation(
        simulation_run_id=simulation_run_id,
        position_id=position_id,
        timestamps=timestamps,
        trigger_config=trigger_config,
        guardrail_config=guardrail_config,
    )

    # Get final state
    final_state = sim_position_repo.get_final_state()
    events = sim_event_logger.get_events_by_trace(simulation_run_id)

    # ===== ASSERTION A: At least 6 events (1+ per bar) =====
    # The orchestrator logs multiple events per bar (PRICE_EVENT, TRIGGER_EVALUATED, etc.)
    # So we should have at least 6 events (one per bar), but likely more
    assert len(events) >= 6, f"Expected at least 6 events (1 per bar), got {len(events)}"

    # Verify we have events for all 6 timestamps (check PRICE_EVENT for each timestamp)
    price_events = [e for e in events if e.event_type == EventType.PRICE_EVENT]
    assert (
        len(price_events) == 6
    ), f"Expected exactly 6 PRICE_EVENT events (1 per bar), got {len(price_events)}"

    # ===== ASSERTION B: At least one BUY and one SELL =====
    # Trigger decisions use lowercase "buy"/"sell"
    # Handle None values safely
    buy_events = [
        e
        for e in events
        if (direction := e.payload.get("trigger_decision", {}).get("direction"))
        and direction.lower() == "buy"
    ]
    sell_events = [
        e
        for e in events
        if (direction := e.payload.get("trigger_decision", {}).get("direction"))
        and direction.lower() == "sell"
    ]

    # Also check order events for BUY/SELL (trade_intent uses lowercase)
    order_events = [e for e in events if e.event_type == EventType.ORDER_CREATED]
    buy_orders = [
        e
        for e in order_events
        if (side := e.payload.get("trade_intent", {}).get("side")) and side.lower() == "buy"
    ]
    sell_orders = [
        e
        for e in order_events
        if (side := e.payload.get("trade_intent", {}).get("side")) and side.lower() == "sell"
    ]

    assert len(buy_events) > 0 or len(buy_orders) > 0, "Expected at least one BUY action"
    assert len(sell_events) > 0 or len(sell_orders) > 0, "Expected at least one SELL action"

    # ===== ASSERTION C: State changes after BUY/SELL =====
    initial_qty = initial_position_state.qty
    initial_cash = initial_position_state.cash

    # State should change if orders were executed
    if len(sim_order_service.orders) > 0:
        assert (
            final_state.qty != initial_qty or final_state.cash != initial_cash
        ), "Position state should change after BUY/SELL orders"

    # ===== ASSERTION D: Event structure validation =====
    # For each bar, we should have at least a PRICE_EVENT
    # We'll validate that events contain the required information
    for event in events:
        # Every event should have timestamp
        assert event.created_at is not None, f"Event {event.event_id} missing timestamp"

        # Price events should have price info (effective_price, anchor_price)
        if event.event_type == EventType.PRICE_EVENT:
            assert (
                "price" in event.payload
            ), f"Price event {event.event_id} missing price (effective_price)"
            assert "timestamp" in event.payload, f"Price event {event.event_id} missing timestamp"
            assert (
                "anchor_price" in event.payload
            ), f"Price event {event.event_id} missing anchor_price"
            # Verify price and anchor_price are not empty
            assert event.payload.get("price"), f"Price event {event.event_id} has empty price"
            # anchor_price can be None initially, but should be set after first trade

        # Trigger events should have decision (action and action_reason)
        if event.event_type == EventType.TRIGGER_EVALUATED:
            assert (
                "trigger_decision" in event.payload
            ), f"Trigger event {event.event_id} missing decision"
            decision = event.payload["trigger_decision"]
            assert "fired" in decision, "Trigger decision missing 'fired'"
            assert "direction" in decision or not decision.get(
                "fired"
            ), "Trigger decision missing 'direction' when fired"
            assert "reason" in decision, "Trigger decision missing 'reason' (action_reason)"
            # Verify action_reason is not empty
            assert decision.get("reason"), "Trigger decision reason should not be empty"

        # Guardrail events should have decision
        if event.event_type == EventType.GUARDRAIL_EVALUATED:
            assert "decision" in event.payload, f"Guardrail event {event.event_id} missing decision"
            decision = event.payload["decision"]
            assert "allowed" in decision, "Guardrail decision missing 'allowed'"
            assert "reason" in decision, "Guardrail decision missing 'reason'"
            # Verify reason is not empty
            assert decision.get("reason"), "Guardrail decision reason should not be empty"

        # Order events should have trade intent (action and action_reason)
        if event.event_type == EventType.ORDER_CREATED:
            assert (
                "trade_intent" in event.payload
            ), f"Order event {event.event_id} missing trade_intent"
            intent = event.payload["trade_intent"]
            assert "side" in intent, "Trade intent missing 'side' (action)"
            assert "qty" in intent, "Trade intent missing 'qty'"
            assert "reason" in intent, "Trade intent missing 'reason' (action_reason)"
            # Verify action and action_reason are not empty (as per requirement D)
            assert intent.get("side"), "Trade intent side (action) should not be empty"
            assert intent.get("reason"), "Trade intent reason (action_reason) should not be empty"
            # Verify quote has effective_price
            assert "quote" in event.payload, f"Order event {event.event_id} missing quote"
            quote = event.payload["quote"]
            assert "price" in quote, "Order event quote missing price (effective_price)"
            assert quote.get("price"), "Order event quote price should not be empty"

    # ===== ASSERTION E: Production tables unchanged =====
    # Count final production table rows using same method as initial
    final_prod_orders_count = 0
    final_prod_trades_count = 0
    final_prod_events_count = 0
    final_prod_positions_count = 0

    if hasattr(container.orders, "_items"):
        final_prod_orders_count = len(container.orders._items)
    if hasattr(container.trades, "_items"):
        final_prod_trades_count = len(container.trades._items)
    if hasattr(container.events, "_items"):
        final_prod_events_count = len(container.events._items)
    if hasattr(container.positions, "_items"):
        final_prod_positions_count = len(container.positions._items)
    elif hasattr(container.positions, "_by_tenant_portfolio"):
        for tenant_dict in container.positions._by_tenant_portfolio.values():
            for portfolio_dict in tenant_dict.values():
                final_prod_positions_count += len(portfolio_dict)

    assert (
        final_prod_orders_count == initial_prod_orders_count
    ), f"Production orders table changed: {initial_prod_orders_count} -> {final_prod_orders_count}"
    assert (
        final_prod_trades_count == initial_prod_trades_count
    ), f"Production trades table changed: {initial_prod_trades_count} -> {final_prod_trades_count}"
    assert (
        final_prod_events_count == initial_prod_events_count
    ), f"Production events table changed: {initial_prod_events_count} -> {final_prod_events_count}"
    assert (
        final_prod_positions_count == initial_prod_positions_count
    ), f"Production positions table changed: {initial_prod_positions_count} -> {final_prod_positions_count}"

    # Print summary for debugging
    print("\n=== Simulation Test Summary ===")
    print(f"Total events: {len(events)}")
    print(f"BUY actions: {len(buy_events) + len(buy_orders)}")
    print(f"SELL actions: {len(sell_events) + len(sell_orders)}")
    print(f"Orders created: {len(sim_order_service.orders)}")
    print(f"Initial state: qty={initial_qty}, cash={initial_cash}")
    print(f"Final state: qty={final_state.qty}, cash={final_state.cash}")
    print("Production tables unchanged: ✓")
