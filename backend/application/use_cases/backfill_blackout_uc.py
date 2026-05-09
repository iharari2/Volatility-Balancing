# =========================
# backend/application/use_cases/backfill_blackout_uc.py
# =========================
"""
Blackout detection and backfill use case.

A "blackout" is a gap in live tick data longer than BLACKOUT_THRESHOLD_HOURS
on a business day.  When a blackout is detected this UC:

  1. Replays daily price evaluations for each missed trading day and records
     them in position_evaluation_timeline with mode='BACKFILL'.  Trades that
     WOULD have fired are noted but position state is NOT changed (too risky
     to retroactively rebalance a live position).

  2. Applies any dividends whose ex-date fell inside the gap — these ARE
     credited to position cash because missing them changes the account balance.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.services.price_trigger import PriceTrigger
from domain.value_objects.configs import GuardrailConfig, TriggerConfig
from domain.value_objects.position_state import PositionState

logger = logging.getLogger(__name__)

# Gaps shorter than this (in calendar days) are treated as weekends / holidays
BLACKOUT_MIN_CALENDAR_DAYS = 2
# Maximum look-back when searching for gaps
DEFAULT_LOOK_BACK_DAYS = 90


# ─── data transfer objects ────────────────────────────────────────────────────

@dataclass
class BlackoutPeriod:
    position_id: str
    ticker: str
    start: datetime   # last recorded tick before the gap
    end: datetime     # first recorded tick after the gap (or now)

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600

    @property
    def calendar_days(self) -> int:
        return (self.end.date() - self.start.date()).days


@dataclass
class MissedDividend:
    ex_date: date
    dps: Decimal
    gross_amount: Decimal
    net_amount: Decimal
    applied: bool = False


@dataclass
class MissedTrade:
    timestamp: datetime
    price: float
    action: str           # WOULD_BUY / WOULD_SELL
    reason: str


@dataclass
class BackfillResult:
    position_id: str
    ticker: str
    blackouts: List[BlackoutPeriod] = field(default_factory=list)
    dividends_applied: List[MissedDividend] = field(default_factory=list)
    ticks_replayed: int = 0
    trades_noted: List[MissedTrade] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_id": self.position_id,
            "ticker": self.ticker,
            "blackouts_found": len(self.blackouts),
            "blackout_periods": [
                {
                    "start": b.start.isoformat(),
                    "end": b.end.isoformat(),
                    "calendar_days": b.calendar_days,
                }
                for b in self.blackouts
            ],
            "dividends_applied": [
                {
                    "ex_date": str(d.ex_date),
                    "dps": float(d.dps),
                    "net_amount": float(d.net_amount),
                    "applied": d.applied,
                }
                for d in self.dividends_applied
            ],
            "ticks_replayed": self.ticks_replayed,
            "trades_would_have_fired": [
                {"timestamp": t.timestamp.isoformat(), "price": t.price, "action": t.action, "reason": t.reason}
                for t in self.trades_noted
            ],
            "errors": self.errors,
        }


# ─── main use case ────────────────────────────────────────────────────────────

class BackfillBlackoutUC:
    """Detect live-data blackouts and backfill dividends + timeline entries."""

    def __init__(
        self,
        positions_repo: Any,
        evaluation_timeline_repo: Any,
        dividend_market_data: Any,
        config_repo: Any,
        look_back_days: int = DEFAULT_LOOK_BACK_DAYS,
    ) -> None:
        self.positions_repo = positions_repo
        self.evaluation_timeline_repo = evaluation_timeline_repo
        self.dividend_market_data = dividend_market_data
        self.config_repo = config_repo
        self.look_back_days = look_back_days

    # ── public API ────────────────────────────────────────────────────────────

    def backfill_all_positions(self) -> List[BackfillResult]:
        """Run backfill for every live position.  Safe to call on schedule."""
        results: List[BackfillResult] = []
        try:
            positions = self._list_all_positions()
        except Exception as exc:
            logger.error("BackfillBlackout: could not list positions: %s", exc)
            return results

        for position in positions:
            if getattr(position, "asset_symbol", None) in (None, "CASH"):
                continue
            try:
                result = self.backfill_position(position)
                results.append(result)
            except Exception as exc:
                logger.error(
                    "BackfillBlackout: unhandled error for %s: %s",
                    getattr(position, "id", "?"),
                    exc,
                    exc_info=True,
                )
        return results

    def backfill_position(self, position: Any) -> BackfillResult:
        """Detect and address blackouts for one position."""
        pid = position.id
        ticker = position.asset_symbol
        result = BackfillResult(position_id=pid, ticker=ticker)

        blackouts = self._find_blackouts(pid, ticker)
        result.blackouts = blackouts

        if not blackouts:
            logger.debug("BackfillBlackout: no blackouts for %s (%s)", ticker, pid[:8])
            return result

        logger.info(
            "BackfillBlackout: %d blackout(s) found for %s — processing",
            len(blackouts),
            ticker,
        )

        trigger_cfg = self._get_trigger_config(pid)
        guardrail_cfg = self._get_guardrail_config(pid)

        for period in blackouts:
            self._process_period(position, period, trigger_cfg, guardrail_cfg, result)

        return result

    # ── gap detection ─────────────────────────────────────────────────────────

    def _find_blackouts(self, position_id: str, ticker: str) -> List[BlackoutPeriod]:
        """Return gaps in position_evaluation_timeline larger than the minimum threshold."""
        since = datetime.now(timezone.utc) - timedelta(days=self.look_back_days)
        gaps: List[BlackoutPeriod] = []

        try:
            from infrastructure.persistence.sql.models import (
                PositionEvaluationTimelineModel,
                get_engine,
            )
            from sqlalchemy import text
            import os

            sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")
            engine = get_engine(sql_url)
            with engine.connect() as conn:
                rows = conn.execute(
                    text(
                        """
                        SELECT DATE(timestamp) as day
                        FROM position_evaluation_timeline
                        WHERE position_id = :pid
                          AND timestamp >= :since
                        GROUP BY DATE(timestamp)
                        ORDER BY day
                        """
                    ),
                    {"pid": position_id, "since": since.isoformat()},
                ).fetchall()
        except Exception as exc:
            logger.error("BackfillBlackout: DB query failed for %s: %s", ticker, exc)
            return gaps

        if not rows:
            return gaps

        # Build list of dates that have ticks
        recorded_days = [datetime.strptime(str(r[0]), "%Y-%m-%d").date() for r in rows]

        # Walk consecutive pairs and flag multi-day gaps that include weekdays
        prev_day = recorded_days[0]
        for cur_day in recorded_days[1:]:
            gap_days = (cur_day - prev_day).days
            if gap_days >= BLACKOUT_MIN_CALENDAR_DAYS and self._has_weekday(prev_day, cur_day):
                gaps.append(
                    BlackoutPeriod(
                        position_id=position_id,
                        ticker=ticker,
                        start=datetime.combine(prev_day, datetime.min.time()).replace(
                            tzinfo=timezone.utc
                        ),
                        end=datetime.combine(cur_day, datetime.min.time()).replace(
                            tzinfo=timezone.utc
                        ),
                    )
                )
            prev_day = cur_day

        # Also check for a trailing gap from last recorded tick to now
        now_date = datetime.now(timezone.utc).date()
        if (now_date - prev_day).days >= BLACKOUT_MIN_CALENDAR_DAYS and self._has_weekday(
            prev_day, now_date
        ):
            gaps.append(
                BlackoutPeriod(
                    position_id=position_id,
                    ticker=ticker,
                    start=datetime.combine(prev_day, datetime.min.time()).replace(
                        tzinfo=timezone.utc
                    ),
                    end=datetime.now(timezone.utc),
                )
            )

        return gaps

    @staticmethod
    def _has_weekday(start: date, end: date) -> bool:
        """Return True if there is at least one weekday (Mon-Fri) strictly between start and end."""
        cur = start + timedelta(days=1)
        while cur < end:
            if cur.weekday() < 5:
                return True
            cur += timedelta(days=1)
        return False

    # ── period processing ─────────────────────────────────────────────────────

    def _process_period(
        self,
        position: Any,
        period: BlackoutPeriod,
        trigger_cfg: Optional[TriggerConfig],
        guardrail_cfg: Optional[GuardrailConfig],
        result: BackfillResult,
    ) -> None:
        ticker = period.ticker

        # 1. Fetch daily prices for the gap
        daily_prices = self._fetch_daily_prices(ticker, period.start, period.end)

        # 2. Replay evaluations
        if daily_prices and trigger_cfg:
            self._replay_ticks(position, period, daily_prices, trigger_cfg, guardrail_cfg, result)

        # 3. Backfill dividends
        self._backfill_dividends(position, period, result)

    # ── price replay ──────────────────────────────────────────────────────────

    def _fetch_daily_prices(
        self, ticker: str, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch daily OHLCV from yfinance for the gap window."""
        try:
            import yfinance as yf

            df = yf.Ticker(ticker).history(
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval="1d",
                auto_adjust=True,
            )
            if df.empty:
                return []
            return [
                {
                    "date": idx.date(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row.get("Volume", 0)),
                }
                for idx, row in df.iterrows()
            ]
        except Exception as exc:
            logger.warning("BackfillBlackout: price fetch failed for %s: %s", ticker, exc)
            return []

    def _replay_ticks(
        self,
        position: Any,
        period: BlackoutPeriod,
        daily_prices: List[Dict[str, Any]],
        trigger_cfg: TriggerConfig,
        guardrail_cfg: Optional[GuardrailConfig],
        result: BackfillResult,
    ) -> None:
        pid = position.id
        ticker = period.ticker
        tenant_id = getattr(position, "tenant_id", "default")
        portfolio_id = getattr(position, "portfolio_id", None)

        anchor = Decimal(str(position.anchor_price or daily_prices[0]["close"]))
        qty = Decimal(str(position.qty or 0))
        cash = Decimal(str(position.cash or 0))

        for bar in daily_prices:
            price = Decimal(str(bar["close"]))
            ts = datetime.combine(bar["date"], datetime.min.time()).replace(
                tzinfo=timezone.utc
            ) + timedelta(hours=21)  # approx market close UTC

            # Trigger check
            trigger_dec = PriceTrigger.evaluate(
                anchor_price=anchor,
                current_price=price,
                config=trigger_cfg,
            )

            # Guardrail check (optional)
            action = "HOLD"
            guardrail_note = ""
            if trigger_dec.fired and guardrail_cfg:
                pos_state = PositionState(ticker=ticker, qty=qty, cash=cash, dividend_receivable=Decimal("0"))
                gd = GuardrailEvaluator.evaluate(
                    position_state=pos_state,
                    trigger_decision=trigger_dec,
                    config=guardrail_cfg,
                    price=price,
                )
                if gd.allowed:
                    action = "WOULD_BUY" if trigger_dec.direction == "buy" else "WOULD_SELL"
                    result.trades_noted.append(
                        MissedTrade(
                            timestamp=ts,
                            price=float(price),
                            action=action,
                            reason=trigger_dec.reason,
                        )
                    )
                    logger.info(
                        "BackfillBlackout: %s %s at %.2f on %s (missed during blackout)",
                        action,
                        ticker,
                        float(price),
                        bar["date"],
                    )
                else:
                    action = "SKIP"
                    guardrail_note = gd.reason or ""
            elif trigger_dec.fired:
                action = "WOULD_BUY" if trigger_dec.direction == "buy" else "WOULD_SELL"

            # Map trigger direction to DB enum values (UP/DOWN/NONE)
            trigger_dir_db = None
            if trigger_dec.direction == "buy":
                trigger_dir_db = "DOWN"
            elif trigger_dec.direction == "sell":
                trigger_dir_db = "UP"
            else:
                trigger_dir_db = "NONE"

            # Write timeline entry
            entry: Dict[str, Any] = {
                "id": f"bfill_{uuid4().hex[:12]}",
                "tenant_id": tenant_id,
                "portfolio_id": portfolio_id,
                "position_id": pid,
                "symbol": ticker,
                "timestamp": ts.isoformat(),
                "mode": "LIVE",           # must match ck_eval_timeline_mode
                "evaluation_type": "DAILY_CHECK",  # must match ck_eval_timeline_evaluation_type
                "close_price": float(price),
                "open_price": bar["open"],
                "high_price": bar["high"],
                "low_price": bar["low"],
                "effective_price": float(price),
                "anchor_price": float(anchor),
                "pct_change_from_anchor": float(
                    (price - anchor) / anchor * 100
                ) if anchor else None,
                "is_market_hours": True,
                "allow_after_hours": True,
                "is_fresh": True,
                "is_inline": True,
                "position_qty_before": float(qty),
                "position_cash_before": float(cash),
                "position_stock_value_before": float(qty * price),
                "position_total_value_before": float(qty * price + cash),
                "position_dividend_receivable_before": 0.0,
                "trigger_fired": trigger_dec.fired,
                "trigger_direction": trigger_dir_db,
                "trigger_reason": trigger_dec.reason,
                "guardrail_notes": guardrail_note,
                "action": "HOLD",         # always HOLD — we do not execute during backfill
                "action_taken": "NO_ACTION",
                "action_reason": "backfill_replay",
                "dividend_declared": False,
                "dividend_applied": False,
                "anchor_updated": False,
                "evaluation_notes": f"Backfilled for blackout {period.start.date()} to {period.end.date()}",
                "source": "backfill",
            }
            try:
                self.evaluation_timeline_repo.save(entry)
                result.ticks_replayed += 1
            except Exception as exc:
                msg = f"Failed to save backfill tick {bar['date']}: {exc}"
                logger.warning("BackfillBlackout: %s", msg)
                result.errors.append(msg)

    # ── dividend backfill ─────────────────────────────────────────────────────

    def _backfill_dividends(
        self,
        position: Any,
        period: BlackoutPeriod,
        result: BackfillResult,
    ) -> None:
        if not self.dividend_market_data:
            return

        ticker = period.ticker
        pid = position.id

        try:
            dividends = self.dividend_market_data.get_dividend_history(
                ticker, period.start, period.end
            )
        except Exception as exc:
            msg = f"Dividend fetch failed for {ticker}: {exc}"
            logger.warning("BackfillBlackout: %s", msg)
            result.errors.append(msg)
            return

        if not dividends:
            return

        qty = Decimal(str(position.qty or 0))
        withholding = Decimal(str(getattr(position, "withholding_tax_rate", 0.25) or 0.25))

        for div in dividends:
            gross = div.dps * qty
            net = gross * (1 - withholding)

            missed = MissedDividend(
                ex_date=div.ex_date.date(),
                dps=div.dps,
                gross_amount=gross,
                net_amount=net,
            )

            # Credit the position cash
            try:
                position.cash = float(Decimal(str(position.cash or 0)) + net)
                self.positions_repo.save(position)
                missed.applied = True
                logger.info(
                    "BackfillBlackout: applied missed dividend for %s ex=%s dps=%.4f net=%.2f",
                    ticker,
                    div.ex_date.date(),
                    float(div.dps),
                    float(net),
                )
            except Exception as exc:
                msg = f"Could not apply dividend ex={div.ex_date.date()} to {ticker}: {exc}"
                logger.error("BackfillBlackout: %s", msg)
                result.errors.append(msg)

            result.dividends_applied.append(missed)

            # Record in timeline
            tenant_id = getattr(position, "tenant_id", "default")
            portfolio_id = getattr(position, "portfolio_id", None)
            ts = div.ex_date.replace(hour=21, minute=0, second=0, microsecond=0)
            entry: Dict[str, Any] = {
                "id": f"bfill_div_{uuid4().hex[:12]}",
                "tenant_id": tenant_id,
                "portfolio_id": portfolio_id,
                "position_id": pid,
                "symbol": ticker,
                "timestamp": ts.isoformat(),
                "mode": "LIVE",
                "evaluation_type": "DIVIDEND",
                "is_market_hours": True,
                "allow_after_hours": True,
                "is_fresh": True,
                "is_inline": True,
                "position_qty_before": float(qty),
                "position_cash_before": float(cash),
                "position_stock_value_before": 0.0,
                "position_total_value_before": float(cash),
                "position_dividend_receivable_before": 0.0,
                "trigger_fired": False,
                "trigger_direction": "NONE",
                "anchor_updated": False,
                "action": "HOLD",
                "action_taken": "NO_ACTION",
                "action_reason": "backfill_dividend",
                "dividend_declared": True,
                "dividend_ex_date": div.ex_date.isoformat(),
                "dividend_pay_date": div.pay_date.isoformat() if div.pay_date else None,
                "dividend_rate": float(div.dps),
                "dividend_gross_value": float(gross),
                "dividend_net_value": float(net),
                "dividend_applied": missed.applied,
                "evaluation_notes": f"Backfilled dividend - missed during blackout {period.start.date()} to {period.end.date()}",
                "source": "backfill",
            }
            try:
                self.evaluation_timeline_repo.save(entry)
            except Exception as exc:
                logger.warning("BackfillBlackout: failed to record dividend timeline entry: %s", exc)

    # ── config helpers ────────────────────────────────────────────────────────

    def _get_trigger_config(self, position_id: str) -> Optional[TriggerConfig]:
        try:
            return self.config_repo.get_trigger_config(position_id)
        except Exception:
            return None

    def _get_guardrail_config(self, position_id: str) -> Optional[GuardrailConfig]:
        try:
            return self.config_repo.get_guardrail_config(position_id)
        except Exception:
            return None

    def _list_all_positions(self) -> List[Any]:
        """Fetch all positions across all tenants/portfolios via raw SQL fallback."""
        import os
        from infrastructure.persistence.sql.models import get_engine
        from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
        from sqlalchemy import text

        sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")
        engine = get_engine(sql_url)
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT tenant_id, portfolio_id FROM positions")
            ).fetchall()

        positions: List[Any] = []
        for tenant_id, portfolio_id in rows:
            try:
                batch = self.positions_repo.list_all(
                    tenant_id=tenant_id, portfolio_id=portfolio_id
                )
                positions.extend(batch)
            except Exception as exc:
                logger.warning(
                    "BackfillBlackout: list_all failed for tenant=%s portfolio=%s: %s",
                    tenant_id, portfolio_id, exc,
                )
        return positions
