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

        # ── Pull evaluation timeline rows ────────────────────────────────────
        price_series: List[PricePoint] = []
        value_series: List[ValuePoint] = []

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

            for r in rows:
                ts = _to_iso(r.get("timestamp"))
                if not ts:
                    continue
                ep = r.get("effective_price") or r.get("price")
                tv = r.get("position_total_value_after") or r.get("position_total_value")
                if ep is not None:
                    try:
                        price_series.append(PricePoint(timestamp=ts, price=float(ep)))
                    except (TypeError, ValueError):
                        pass
                if tv is not None:
                    try:
                        value_series.append(ValuePoint(timestamp=ts, value=float(tv)))
                    except (TypeError, ValueError):
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
                    for o in orders:
                        ts = _to_iso(o.created_at)
                        if ts and o.qty and o.avg_fill_price:
                            trade_markers.append(TradeMarker(
                                timestamp=ts,
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
