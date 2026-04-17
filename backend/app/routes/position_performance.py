"""
Position performance endpoint — all data from position_evaluation_timeline.
No yfinance calls; effective_price stored at each evaluation is used as the price series.
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
    stock_value: Optional[float] = None


class TradeMarker(BaseModel):
    timestamp: str
    side: str          # BUY | SELL
    qty: float
    price: float
    commission: Optional[float] = None


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

        price_series: List[PricePoint] = []
        value_series: List[ValuePoint] = []
        anchor_series: List[AnchorPoint] = []
        trade_markers: List[TradeMarker] = []

        # Current-state values taken from the most recent timeline row
        last_anchor: Optional[float] = None
        last_trigger_up_pct: Optional[float] = None
        last_trigger_down_pct: Optional[float] = None
        last_min_pct: Optional[float] = None
        last_max_pct: Optional[float] = None
        last_stock_pct: Optional[float] = None

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
            # list_by_position returns newest-first; reverse to chronological
            rows = list(reversed(rows))

            # Downsample to max_points while preserving trade rows
            if len(rows) > max_points:
                step = max(1, len(rows) // max_points)
                trade_indices = {i for i, r in enumerate(rows) if r.get("action") in ("BUY", "SELL")}
                downsampled = [r for i, r in enumerate(rows) if i % step == 0 or i in trade_indices]
                rows = downsampled

            prev_anchor: Optional[float] = None
            for r in rows:
                ts = _to_iso(r.get("timestamp"))
                if not ts:
                    continue

                # Price series — effective_price is the market price at eval time
                ep = r.get("effective_price")
                if ep is not None:
                    try:
                        price_series.append(PricePoint(timestamp=ts, price=float(ep)))
                    except (TypeError, ValueError):
                        pass

                # Value series — prefer after-state, fall back to before
                tv = r.get("position_total_value_after") or r.get("position_total_value_before")
                sv = r.get("position_stock_value_after") or r.get("position_stock_value_before")
                if tv is not None:
                    try:
                        value_series.append(ValuePoint(
                            timestamp=ts,
                            value=float(tv),
                            stock_value=float(sv) if sv is not None else None,
                        ))
                    except (TypeError, ValueError):
                        pass

                # Anchor series — emit a point only when anchor changes
                ap = r.get("anchor_price")
                if ap is not None:
                    try:
                        ap_float = float(ap)
                        if ap_float != prev_anchor:
                            anchor_series.append(AnchorPoint(timestamp=ts, anchor_price=ap_float))
                            prev_anchor = ap_float
                        last_anchor = ap_float
                    except (TypeError, ValueError):
                        pass

                # Trade markers — exact timestamp, no snapping needed
                action = r.get("action", "")
                if action in ("BUY", "SELL"):
                    exec_qty = r.get("execution_qty") or r.get("trade_intent_qty")
                    exec_price = r.get("execution_price") or ep
                    commission = r.get("execution_commission")
                    if exec_qty is not None and exec_price is not None:
                        try:
                            trade_markers.append(TradeMarker(
                                timestamp=ts,
                                side=action,
                                qty=abs(float(exec_qty)),
                                price=float(exec_price),
                                commission=float(commission) if commission is not None else None,
                            ))
                        except (TypeError, ValueError):
                            pass

                # Track latest config values for AnchorInfo / GuardrailInfo
                if r.get("trigger_up_threshold") is not None:
                    last_trigger_up_pct = float(r["trigger_up_threshold"])
                if r.get("trigger_down_threshold") is not None:
                    last_trigger_down_pct = float(r["trigger_down_threshold"])
                if r.get("guardrail_min_stock_pct") is not None:
                    last_min_pct = float(r["guardrail_min_stock_pct"])
                if r.get("guardrail_max_stock_pct") is not None:
                    last_max_pct = float(r["guardrail_max_stock_pct"])

            # current_stock_pct from last row
            if rows:
                last_row = rows[-1]
                sp = last_row.get("position_stock_pct_after") or last_row.get("position_stock_pct_before")
                if sp is not None:
                    try:
                        last_stock_pct = float(sp)
                    except (TypeError, ValueError):
                        pass

        # Fall back to position/config for anchor if timeline has no rows
        if last_anchor is None:
            last_anchor = position.anchor_price or position.avg_cost
        if last_trigger_up_pct is None or last_trigger_down_pct is None:
            try:
                cfg = portfolio_service._portfolio_config_repo.get(
                    tenant_id=tenant_id, portfolio_id=portfolio_id
                )
                if cfg:
                    last_trigger_up_pct = last_trigger_up_pct or cfg.trigger_up_pct
                    last_trigger_down_pct = last_trigger_down_pct or cfg.trigger_down_pct
                    last_min_pct = last_min_pct or cfg.min_stock_pct
                    last_max_pct = last_max_pct or cfg.max_stock_pct
            except Exception:
                pass

        trigger_up_price = None
        trigger_down_price = None
        if last_anchor and last_trigger_up_pct is not None:
            trigger_up_price = last_anchor * (1 + last_trigger_up_pct / 100)
        if last_anchor and last_trigger_down_pct is not None:
            trigger_down_price = last_anchor * (1 + last_trigger_down_pct / 100)

        return PerformanceResponse(
            ticker=position.asset_symbol,
            window=window,
            price_series=price_series,
            value_series=value_series,
            trade_markers=trade_markers,
            anchor_series=anchor_series,
            anchor=AnchorInfo(
                price=last_anchor,
                trigger_up_pct=last_trigger_up_pct,
                trigger_down_pct=last_trigger_down_pct,
                trigger_up_price=trigger_up_price,
                trigger_down_price=trigger_down_price,
            ),
            guardrails=GuardrailInfo(
                min_stock_pct=last_min_pct,
                max_stock_pct=last_max_pct,
                current_stock_pct=last_stock_pct,
            ),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error fetching performance: {exc}") from exc
