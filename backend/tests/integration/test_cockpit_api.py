# =========================
# backend/tests/integration/test_cockpit_api.py
# =========================
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List

from app.routes.portfolio_cockpit_api import get_position_cockpit

from app.di import container
from application.services.portfolio_service import PortfolioService
from application.use_cases.evaluate_position_uc import EvaluatePositionUC
from application.ports.market_data import IHistoricalPriceProvider
from domain.ports.market_data import MarketDataRepo, PriceData, PriceSource, MarketStatus
from domain.value_objects.configs import TriggerConfig, GuardrailConfig, OrderPolicyConfig
from domain.value_objects.market import MarketQuote
from domain.ports.config_repo import ConfigScope
from domain.ports.evaluation_timeline_repo import EvaluationTimelineRepo


class FakeHistoricalPriceProvider(IHistoricalPriceProvider):
    def __init__(self, ticker: str, timeline: Dict[datetime, Decimal]):
        self._ticker = ticker
        self._timeline = timeline

    def get_quote_at(self, ticker: str, ts: datetime) -> MarketQuote:
        price = self._timeline[ts]
        return MarketQuote(ticker=ticker, price=price, timestamp=ts)


class FakeMarketDataProvider(MarketDataRepo):
    def __init__(self, historical_provider: FakeHistoricalPriceProvider):
        self._historical_provider = historical_provider
        self._current_ts: datetime | None = None

    def set_timestamp(self, ts: datetime) -> None:
        self._current_ts = ts

    def get_price(self, ticker: str) -> PriceData | None:
        return self.get_reference_price(ticker)

    def get_market_status(self) -> MarketStatus:
        return MarketStatus(is_open=True)

    def validate_price(
        self, price_data: PriceData, allow_after_hours: bool = False
    ) -> Dict[str, List[str]]:
        return {"valid": True, "rejections": [], "warnings": []}

    def get_reference_price(self, ticker: str) -> PriceData | None:
        if self._current_ts is None:
            return None
        quote = self._historical_provider.get_quote_at(ticker, self._current_ts)
        price_data = PriceData(
            ticker=ticker,
            price=float(quote.price),
            source=PriceSource.LAST_TRADE,
            timestamp=quote.timestamp,
            is_market_hours=True,
            is_fresh=True,
            is_inline=True,
        )
        # Provide OHLCV fields expected by timeline builder
        price_data.open = float(quote.price)
        price_data.high = float(quote.price)
        price_data.low = float(quote.price)
        price_data.close = float(quote.price)
        price_data.volume = 0
        price_data.bid = float(quote.price)
        price_data.ask = float(quote.price)
        return price_data


class InMemoryEvaluationTimelineRepo(EvaluationTimelineRepo):
    def __init__(self):
        self._rows: List[Dict[str, object]] = []

    def save(self, evaluation_data: Dict[str, object]) -> str:
        row_id = str(evaluation_data.get("id") or f"row_{len(self._rows) + 1}")
        record = dict(evaluation_data)
        record["id"] = row_id
        self._rows.append(record)
        return row_id

    def get_by_id(self, evaluation_id: str) -> Dict[str, object] | None:
        return next((row for row in self._rows if row.get("id") == evaluation_id), None)

    def list_by_position(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        mode: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
    ) -> List[Dict[str, object]]:
        rows = [
            row
            for row in self._rows
            if row.get("tenant_id") == tenant_id
            and row.get("portfolio_id") == portfolio_id
            and row.get("position_id") == position_id
            and (mode is None or row.get("mode") == mode)
        ]
        if start_date:
            rows = [row for row in rows if row.get("timestamp") and row["timestamp"] >= start_date]
        if end_date:
            rows = [row for row in rows if row.get("timestamp") and row["timestamp"] <= end_date]
        rows.sort(key=lambda row: row.get("timestamp") or datetime.min, reverse=True)
        if limit:
            rows = rows[:limit]
        return rows

    def list_by_portfolio(
        self,
        tenant_id: str,
        portfolio_id: str,
        mode: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
    ) -> List[Dict[str, object]]:
        rows = [
            row
            for row in self._rows
            if row.get("tenant_id") == tenant_id
            and row.get("portfolio_id") == portfolio_id
            and (mode is None or row.get("mode") == mode)
        ]
        if start_date:
            rows = [row for row in rows if row.get("timestamp") and row["timestamp"] >= start_date]
        if end_date:
            rows = [row for row in rows if row.get("timestamp") and row["timestamp"] <= end_date]
        rows.sort(key=lambda row: row.get("timestamp") or datetime.min, reverse=True)
        if limit:
            rows = rows[:limit]
        return rows

    def list_by_trace_id(self, trace_id: str) -> List[Dict[str, object]]:
        return [row for row in self._rows if row.get("trace_id") == trace_id]

    def list_by_simulation_run(self, simulation_run_id: str, limit: int | None = None) -> List[Dict[str, object]]:
        rows = [row for row in self._rows if row.get("simulation_run_id") == simulation_run_id]
        if limit:
            rows = rows[:limit]
        return rows


def test_cockpit_endpoint_returns_buy_and_sell_timeline() -> None:
    tenant_id = "default"
    ticker = "TEST"

    # Create portfolio with one position (independent cash bucket)
    portfolio_service = PortfolioService(
        portfolio_repo=container.portfolio_repo,
        positions_repo=container.positions,
        portfolio_config_repo=container.portfolio_config_repo,
        baseline_repo=container.position_baseline,
        market_data_repo=None,
    )

    portfolio = portfolio_service.create_portfolio(
        tenant_id=tenant_id,
        name=f"Test Cockpit {datetime.now(timezone.utc).isoformat()}",
        description="Cockpit integration test",
        user_id="default",
        portfolio_type="LIVE",
        trading_hours_policy="OPEN_ONLY",
        starting_cash={"currency": "USD", "amount": 0.0},
        holdings=[
            {
                "asset": ticker,
                "qty": 10.0,
                "anchor_price": 100.0,
                "avg_cost": 100.0,
                "cash": 1000.0,
            }
        ],
        template="DEFAULT",
    )

    positions = container.positions.list_all(tenant_id=tenant_id, portfolio_id=portfolio.id)
    assert positions, "Expected position to be created"
    position_id = positions[0].id

    # Configure trigger/guardrail thresholds via config store (not Position state)
    container.config.set_trigger_config(
        position_id,
        TriggerConfig(up_threshold_pct=Decimal("5"), down_threshold_pct=Decimal("5")),
    )
    container.config.set_guardrail_config(
        position_id,
        GuardrailConfig(
            min_stock_pct=Decimal("0.2"),
            max_stock_pct=Decimal("0.8"),
            max_trade_pct_of_position=Decimal("0.5"),
        ),
    )
    container.config.set_order_policy_config(
        position_id,
        OrderPolicyConfig(
            min_qty=Decimal("0"),
            min_notional=Decimal("0"),
            rebalance_ratio=Decimal("1.0"),
            allow_after_hours=True,
            commission_rate=Decimal("0"),
        ),
    )
    container.config.set_commission_rate(
        rate=0.0,
        scope=ConfigScope.TENANT_ASSET,
        tenant_id=tenant_id,
        asset_id=ticker,
    )

    # Create deterministic intraday timeline (10 bars)
    base_ts = datetime(2024, 1, 2, 14, 30, tzinfo=timezone.utc)
    prices = [100, 94, 96, 106, 103, 97, 108, 102, 95, 105]
    timestamps = [base_ts + timedelta(minutes=idx) for idx in range(len(prices))]
    timeline = {ts: Decimal(str(price)) for ts, price in zip(timestamps, prices)}

    historical_provider = FakeHistoricalPriceProvider(ticker, timeline)
    market_provider = FakeMarketDataProvider(historical_provider)
    container.market_data = market_provider
    container.evaluation_timeline = InMemoryEvaluationTimelineRepo()

    cockpit_service = PortfolioService(
        portfolio_repo=container.portfolio_repo,
        positions_repo=container.positions,
        portfolio_config_repo=container.portfolio_config_repo,
        baseline_repo=container.position_baseline,
        market_data_repo=market_provider,
    )

    evaluate_uc = EvaluatePositionUC(
        positions=container.positions,
        events=container.events,
        market_data=market_provider,
        clock=container.clock,
        trigger_config_provider=container.trigger_config_provider,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
        config_repo=container.config,
        portfolio_repo=container.portfolio_repo,
        evaluation_timeline_repo=container.evaluation_timeline,
    )

    for ts in timestamps:
        market_provider.set_timestamp(ts)
        evaluate_uc.evaluate_with_market_data(
            tenant_id=tenant_id, portfolio_id=portfolio.id, position_id=position_id
        )

    cockpit = get_position_cockpit(
        portfolio_id=portfolio.id,
        position_id=position_id,
        window="4000d",
        tenant_id=tenant_id,
        timeline_limit=200,
        quote_limit=20,
        portfolio_service=cockpit_service,
    )
    timeline_rows = cockpit.timeline_rows
    actions = {row.get("action") for row in timeline_rows}
    assert "BUY" in actions
    assert "SELL" in actions
