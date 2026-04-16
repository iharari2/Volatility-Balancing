"""
Position performance endpoint — returns ticker price series, reconstructed
position value series, and trade markers for the combo chart.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user
from app.di import container
from app.routes.portfolios import get_portfolio_service
from application.services.portfolio_service import PortfolioService

router = APIRouter(
    prefix="/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}",
    tags=["performance"],
)

_WINDOW_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])$")


def _parse_window(window: str) -> Optional[timedelta]:
    if not window:
        return None
    w = window.strip().lower()
    if w == "all":
        return None
    m = _WINDOW_RE.match(w)
    if not m:
        return None
    v, u = int(m.group("value")), m.group("unit")
    return {"s": timedelta(seconds=v), "m": timedelta(minutes=v),
            "h": timedelta(hours=v), "d": timedelta(days=v),
            "w": timedelta(weeks=v)}.get(u)


def _to_iso(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


class PricePoint(BaseModel):
    timestamp: str
    price: float


class ValuePoint(BaseModel):
    timestamp: str
    value: float


class TradeMarker(BaseModel):
    timestamp: str
    side: str          # BUY | SELL
    qty: float
    price: float


class AnchorPoint(BaseModel):
    timestamp: str
    anchor_price: float


class AnchorInfo(BaseModel):
    price: Optional[float]
    trigger_up_pct: Optional[float]
    trigger_down_pct: Optional[float]
    trigger_up_price: Optional[float]
    trigger_down_price: Optional[float]


class GuardrailInfo(BaseModel):
    min_stock_pct: Optional[float]
    max_stock_pct: Optional[float]
    current_stock_pct: Optional[float]


class PerformanceResponse(BaseModel):
    ticker: str
    window: str
    price_series: List[PricePoint]
    value_series: List[ValuePoint]
    trade_markers: List[TradeMarker]
    anchor: AnchorInfo
    anchor_series: List[AnchorPoint]
    guardrails: GuardrailInfo


@router.get("/performance", response_model=PerformanceResponse)
def get_position_performance(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    window: str = Query("7d"),
    max_points: int = Query(500),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    user: CurrentUser = Depends(get_current_user),
) -> PerformanceResponse:
    try:
        if isinstance(user, CurrentUser):
            tenant_id = user.tenant_id

        position = portfolio_service._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        delta = _parse_window(window)
        now = datetime.now(timezone.utc)
        start_ts = now - delta if delta else None

        # ── Pull evaluation timeline rows (for position value series + anchor) ──
        price_series: List[PricePoint] = []
        value_series: List[ValuePoint] = []
        anchor_series: List[AnchorPoint] = []

        if hasattr(container, "evaluation_timeline"):
            rows: List[Dict[str, Any]] = container.evaluation_timeline.list_by_position(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position_id=position_id,
                mode="LIVE",
                start_date=start_ts,
                end_date=now,
                limit=10000,
            )
            # rows are newest-first from the timeline; reverse to chronological
            rows = list(reversed(rows))

            # Downsample if needed
            if len(rows) > max_points:
                step = len(rows) // max_points
                rows = rows[::step]

            prev_anchor: Optional[float] = None
            for r in rows:
                ts = _to_iso(r.get("timestamp"))
                if not ts:
                    continue
                tv = r.get("position_total_value_after") or r.get("position_total_value")
                if tv is not None:
                    try:
                        value_series.append(ValuePoint(timestamp=ts, value=float(tv)))
                    except (TypeError, ValueError):
                        pass
                # Build anchor series: emit a point whenever anchor changes
                ap = r.get("anchor_price")
                if ap is not None:
                    try:
                        ap_float = float(ap)
                        if ap_float != prev_anchor:
                            anchor_series.append(AnchorPoint(timestamp=ts, anchor_price=ap_float))
                            prev_anchor = ap_float
                    except (TypeError, ValueError):
                        pass

        # ── Market price series from yfinance (always real market data) ──────
        try:
            import yfinance as yf
            ticker_sym = position.asset_symbol
            # Map window to yfinance period + interval
            _yf_params = {
                "1d":  ("1d",   "5m"),
                "7d":  ("7d",   "1h"),
                "30d": ("1mo",  "1d"),
                "90d": ("3mo",  "1d"),
                "all": ("max",  "1wk"),
            }
            yf_period, yf_interval = _yf_params.get(window, ("1mo", "1d"))
            hist = yf.Ticker(ticker_sym).history(period=yf_period, interval=yf_interval)
            if not hist.empty:
                for idx, row in hist.iterrows():
                    ts_val = idx
                    if hasattr(ts_val, 'to_pydatetime'):
                        ts_val = ts_val.to_pydatetime()
                    if hasattr(ts_val, 'isoformat'):
                        ts_iso = ts_val.isoformat()
                    else:
                        ts_iso = str(ts_val)
                    close_price = float(row["Close"])
                    price_series.append(PricePoint(timestamp=ts_iso, price=close_price))
        except Exception:
            pass

        # ── Trade markers from orders ────────────────────────────────────────
        trade_markers: List[TradeMarker] = []
        try:
            from infrastructure.persistence.sql.models import OrderModel
            from sqlalchemy import select

            if hasattr(portfolio_service._positions_repo, "_sf"):
                with portfolio_service._positions_repo._sf() as session:
                    stmt = select(OrderModel).where(
                        OrderModel.position_id == position_id,
                        OrderModel.status == "FILLED",
                    )
                    if start_ts:
                        stmt = stmt.where(OrderModel.created_at >= start_ts)
                    stmt = stmt.order_by(OrderModel.created_at.asc())
                    orders = session.execute(stmt).scalars().all()

                    # Build sorted price-series timestamps for snapping
                    price_ts_sorted: List[datetime] = []
                    for p in price_series:
                        try:
                            from datetime import timezone as _tz
                            dt = datetime.fromisoformat(p.timestamp)
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            price_ts_sorted.append(dt)
                        except Exception:
                            pass
                    price_ts_sorted.sort()

                    for o in orders:
                        if not (o.qty and o.avg_fill_price):
                            continue
                        raw_ts = o.created_at
                        if raw_ts is None:
                            continue
                        if isinstance(raw_ts, str):
                            try:
                                raw_ts = datetime.fromisoformat(raw_ts)
                            except Exception:
                                continue
                        if hasattr(raw_ts, 'tzinfo') and raw_ts.tzinfo is None:
                            raw_ts = raw_ts.replace(tzinfo=timezone.utc)

                        # Snap to nearest price series timestamp (within 4 hours)
                        snapped_ts = raw_ts
                        if price_ts_sorted:
                            nearest = min(price_ts_sorted, key=lambda t: abs((t - raw_ts).total_seconds()))
                            if abs((nearest - raw_ts).total_seconds()) <= 4 * 3600:
                                snapped_ts = nearest

                        ts_iso = _to_iso(snapped_ts)
                        if ts_iso:
                            trade_markers.append(TradeMarker(
                                timestamp=ts_iso,
                                side=o.side.upper() if o.side else "BUY",
                                qty=abs(float(o.qty)),
                                price=float(o.avg_fill_price),
                            ))
        except Exception:
            pass

        # ── Anchor + guardrails from cockpit ─────────────────────────────────
        cockpit = portfolio_service.get_position_cockpit(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        anchor_price = position.anchor_price or position.avg_cost
        trigger_up_pct: Optional[float] = None
        trigger_down_pct: Optional[float] = None
        trigger_up_price: Optional[float] = None
        trigger_down_price: Optional[float] = None
        min_pct: Optional[float] = None
        max_pct: Optional[float] = None
        current_stock_pct: Optional[float] = None

        if cockpit:
            guardrails = cockpit.get("guardrails") or {}
            min_pct = guardrails.get("min_stock_pct")
            max_pct = guardrails.get("max_stock_pct")
            alloc = cockpit.get("stock_allocation") or {}
            current_stock_pct = alloc.get("stock_allocation_pct")

        try:
            cfg = portfolio_service._portfolio_config_repo.get(
                tenant_id=tenant_id, portfolio_id=portfolio_id
            )
            if cfg:
                trigger_up_pct = cfg.trigger_up_pct
                trigger_down_pct = cfg.trigger_down_pct
                if anchor_price:
                    trigger_up_price = anchor_price * (1 + trigger_up_pct / 100)
                    trigger_down_price = anchor_price * (1 + trigger_down_pct / 100)
                if min_pct is None:
                    min_pct = cfg.min_stock_pct
                    max_pct = cfg.max_stock_pct
        except Exception:
            pass

        return PerformanceResponse(
            ticker=position.asset_symbol,
            window=window,
            price_series=price_series,
            value_series=value_series,
            trade_markers=trade_markers,
            anchor_series=anchor_series,
            anchor=AnchorInfo(
                price=anchor_price,
                trigger_up_pct=trigger_up_pct,
                trigger_down_pct=trigger_down_pct,
                trigger_up_price=trigger_up_price,
                trigger_down_price=trigger_down_price,
            ),
            guardrails=GuardrailInfo(
                min_stock_pct=min_pct,
                max_stock_pct=max_pct,
                current_stock_pct=current_stock_pct,
            ),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error fetching performance: {exc}") from exc
