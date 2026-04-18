# =========================
# backend/app/routes/portfolio_cockpit_api.py
# =========================
"""
Portfolio-scoped cockpit API endpoints.

These endpoints provide the Position Cockpit contract required by the Trade screen.
They are intentionally tenant-agnostic and default to tenant_id="default".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.di import container
from app.auth import get_current_user, CurrentUser
from application.services.portfolio_service import PortfolioService
from app.routes.portfolios import get_portfolio_service

router = APIRouter(prefix="/api", tags=["portfolio-cockpit"])

_WINDOW_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])$")


def _parse_window(window: str) -> Optional[timedelta]:
    if not window:
        return None
    window_lower = window.strip().lower()
    # Handle "all" as no time filter
    if window_lower == "all":
        return None
    match = _WINDOW_RE.match(window_lower)
    if not match:
        return None
    value = int(match.group("value"))
    unit = match.group("unit")
    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)
    if unit == "w":
        return timedelta(weeks=value)
    return None


def _to_iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class PortfolioListItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str


class LastAction(BaseModel):
    action: Optional[str]
    timestamp: Optional[str]
    reason: Optional[str]


class PositionSummaryItem(BaseModel):
    position_id: str
    asset_symbol: str
    qty: float
    cash: float
    last_price: Optional[float]
    anchor_price: Optional[float]
    avg_cost: Optional[float]
    stock_value: float
    total_value: float
    stock_pct: Optional[float]
    position_vs_baseline_pct: Optional[float]
    stock_vs_baseline_pct: Optional[float]
    status: Optional[str]
    # Guardrails
    guardrail_min_pct: Optional[float]
    guardrail_max_pct: Optional[float]
    # Trigger distance from anchor (positive = above anchor, negative = below)
    pct_from_anchor: Optional[float]
    trigger_up_pct: Optional[float]
    trigger_down_pct: Optional[float]
    # Last robot action
    last_action: Optional[LastAction]


class PositionSummaryDetail(BaseModel):
    position_id: str
    asset_symbol: str
    qty: float
    cash: float
    last_price: Optional[float]
    stock_value: float
    total_value: float
    anchor_price: Optional[float]
    avg_cost: Optional[float]


class BaselineComparison(BaseModel):
    baseline_price: Optional[float]
    baseline_total_value: Optional[float]
    baseline_stock_value: Optional[float]
    position_vs_baseline_pct: Optional[float]
    position_vs_baseline_abs: Optional[float]
    stock_vs_baseline_pct: Optional[float]
    stock_vs_baseline_abs: Optional[float]


class AllocationBand(BaseModel):
    min_stock_pct: Optional[float]
    max_stock_pct: Optional[float]
    current_stock_pct: Optional[float]
    within_band: Optional[bool]


class RecentQuote(BaseModel):
    timestamp: Optional[str]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    effective_price: Optional[float]
    session: Optional[str]
    price_policy: Optional[str]


class CockpitResponse(BaseModel):
    position_summary: PositionSummaryDetail
    baseline_comparison: BaselineComparison
    allocation_band: AllocationBand
    recent_quotes: List[RecentQuote]
    timeline_rows: List[Dict[str, Any]]


@router.get("/portfolios", response_model=List[PortfolioListItem])
def list_portfolios(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    user: CurrentUser = Depends(get_current_user),
) -> List[PortfolioListItem]:
    try:
        tenant_id = user.tenant_id
        portfolios = portfolio_service.list_portfolios(tenant_id=tenant_id)
        return [
            PortfolioListItem(
                id=p.id,
                name=p.name,
                description=p.description,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
            for p in portfolios
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error listing portfolios: {exc}") from exc


@router.get(
    "/portfolios/{portfolio_id}/positions",
    response_model=List[PositionSummaryItem],
)
def list_positions_for_portfolio(
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    user: CurrentUser = Depends(get_current_user),
) -> List[PositionSummaryItem]:
    """Return position summaries using only DB data (no live market calls).

    Live market prices are intentionally excluded here to keep this endpoint
    fast.  The workspace fetches fresh price data for the *selected* position
    via the per-position cockpit endpoint.
    """
    try:
        tenant_id = user.tenant_id
        positions = portfolio_service.get_portfolio_positions(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )

        # Batch-fetch per-position guardrail + trigger configs (one query each)
        pos_guardrail_map: dict = {}
        pos_trigger_map: dict = {}
        try:
            from infrastructure.persistence.sql.models import GuardrailConfigModel, TriggerConfigModel
            from sqlalchemy import select as _gsel
            pos_ids = [p.id for p in positions]
            if pos_ids and hasattr(container.config, "_sf"):
                with container.config._sf() as _gs:
                    _rows = _gs.execute(
                        _gsel(GuardrailConfigModel).where(GuardrailConfigModel.position_id.in_(pos_ids))
                    ).scalars().all()
                    for r in _rows:
                        pos_guardrail_map[r.position_id] = r
                with container.config._sf() as _ts:
                    _trows = _ts.execute(
                        _gsel(TriggerConfigModel).where(TriggerConfigModel.position_id.in_(pos_ids))
                    ).scalars().all()
                    for r in _trows:
                        pos_trigger_map[r.position_id] = r
        except Exception:
            pass

        # Batch-fetch trading status for all positions in one query
        status_map: dict = {}
        try:
            if hasattr(portfolio_service._positions_repo, "_sf"):
                from infrastructure.persistence.sql.models import PositionModel
                from sqlalchemy import select as _select
                with portfolio_service._positions_repo._sf() as session:
                    rows = session.execute(
                        _select(PositionModel.id, PositionModel.status).where(
                            PositionModel.portfolio_id == portfolio_id
                        )
                    ).all()
                    status_map = {r.id: r.status for r in rows if r.status}
        except Exception:
            pass

        # Batch-fetch last BUY/SELL for all positions in one timeline query
        last_action_map: dict = {}
        try:
            if hasattr(container, "evaluation_timeline"):
                trade_rows = container.evaluation_timeline.list_by_portfolio(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio_id,
                    mode="LIVE",
                    action_filter=["BUY", "SELL"],
                    limit=max(len(positions) * 50, 200),
                )
                # Already ordered by timestamp desc — take first occurrence per position
                for row in trade_rows:
                    pid = row.get("position_id")
                    if pid and pid not in last_action_map:
                        last_action_map[pid] = row
        except Exception:
            pass

        results: List[PositionSummaryItem] = []
        for position in positions:
            # Use stored price — no yfinance calls on the list endpoint
            price = position.anchor_price or position.avg_cost

            stock_value = (price or 0.0) * position.qty
            total_value = position.cash + stock_value
            stock_pct = (stock_value / total_value * 100) if total_value > 0 else None

            # Guardrail / trigger config — per-position only, hardcoded defaults as fallback
            guardrail_min_pct: Optional[float] = None
            guardrail_max_pct: Optional[float] = None
            trigger_up_pct: Optional[float] = None
            trigger_down_pct: Optional[float] = None
            try:
                pg = pos_guardrail_map.get(position.id)
                if pg:
                    guardrail_min_pct = float(pg.min_stock_pct) * 100
                    guardrail_max_pct = float(pg.max_stock_pct) * 100
                else:
                    guardrail_min_pct = 25.0
                    guardrail_max_pct = 75.0
                pt = pos_trigger_map.get(position.id)
                if pt:
                    trigger_up_pct = float(pt.up_threshold_pct)
                    trigger_down_pct = float(pt.down_threshold_pct)
                else:
                    trigger_up_pct = 3.0
                    trigger_down_pct = -3.0
            except Exception:
                pass

            status: Optional[str] = status_map.get(position.id, "RUNNING")

            r = last_action_map.get(position.id)
            last_action_obj = (
                LastAction(
                    action=r.get("action"),
                    timestamp=_to_iso(r.get("timestamp")),
                    reason=r.get("reason") or r.get("action_reason"),
                )
                if r else None
            )

            results.append(
                PositionSummaryItem(
                    position_id=position.id,
                    asset_symbol=position.asset_symbol,
                    qty=position.qty,
                    cash=position.cash,
                    last_price=price,
                    anchor_price=position.anchor_price,
                    avg_cost=position.avg_cost,
                    stock_value=stock_value,
                    total_value=total_value,
                    stock_pct=stock_pct,
                    position_vs_baseline_pct=None,
                    stock_vs_baseline_pct=None,
                    status=status,
                    guardrail_min_pct=guardrail_min_pct,
                    guardrail_max_pct=guardrail_max_pct,
                    pct_from_anchor=None,  # updated by workspace when position is selected
                    trigger_up_pct=trigger_up_pct,
                    trigger_down_pct=trigger_down_pct,
                    last_action=last_action_obj,
                )
            )

        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error listing positions: {exc}") from exc


@router.get(
    "/portfolios/{portfolio_id}/positions/{position_id}/cockpit",
    response_model=CockpitResponse,
)
def get_position_cockpit(
    portfolio_id: str,
    position_id: str,
    window: str = Query("7d", description="Timeline window, e.g. 7d, 24h"),
    tenant_id: str = Query("default", description="Tenant scope (overridden by auth)"),
    timeline_limit: int = Query(10000, description="Max timeline rows to return"),
    quote_limit: int = Query(20, description="Max recent quotes to return"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    user: CurrentUser = Depends(get_current_user),
) -> CockpitResponse:
    try:
        if isinstance(user, CurrentUser):
            tenant_id = user.tenant_id
        cockpit = portfolio_service.get_position_cockpit(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not cockpit:
            raise HTTPException(status_code=404, detail="Position not found")

        position = cockpit["position"]
        price = None
        if cockpit.get("current_market_data"):
            price = cockpit["current_market_data"].get("price")
        if price is None:
            price = position.get("anchor_price") or position.get("avg_cost")

        stock_value = (price or 0.0) * position["qty"]
        total_value = position["cash"] + stock_value

        position_summary = PositionSummaryDetail(
            position_id=position["id"],
            asset_symbol=position["asset_symbol"],
            qty=position["qty"],
            cash=position["cash"],
            last_price=price,
            stock_value=stock_value,
            total_value=total_value,
            anchor_price=position.get("anchor_price"),
            avg_cost=position.get("avg_cost"),
        )

        baseline = cockpit.get("baseline") or {}
        baseline_comparison = BaselineComparison(
            baseline_price=baseline.get("baseline_price"),
            baseline_total_value=baseline.get("baseline_total_value"),
            baseline_stock_value=baseline.get("baseline_stock_value"),
            position_vs_baseline_pct=cockpit.get("position_vs_baseline", {}).get("pct"),
            position_vs_baseline_abs=cockpit.get("position_vs_baseline", {}).get("abs"),
            stock_vs_baseline_pct=cockpit.get("stock_vs_baseline", {}).get("pct"),
            stock_vs_baseline_abs=cockpit.get("stock_vs_baseline", {}).get("abs"),
        )

        allocation = cockpit.get("stock_allocation") or {}
        guardrails = cockpit.get("guardrails") or {}
        allocation_band = AllocationBand(
            min_stock_pct=guardrails.get("min_stock_pct"),
            max_stock_pct=guardrails.get("max_stock_pct"),
            current_stock_pct=allocation.get("stock_allocation_pct"),
            within_band=cockpit.get("allocation_within_guardrails"),
        )

        recent_quotes: List[RecentQuote] = []
        market_data = portfolio_service.get_position_market_data(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            limit=quote_limit,
        )
        if market_data:
            latest = market_data.get("latest")
            if latest:
                recent_quotes.append(
                    RecentQuote(
                        timestamp=_to_iso(latest.get("timestamp")),
                        open=latest.get("open_price"),
                        high=latest.get("high_price"),
                        low=latest.get("low_price"),
                        close=latest.get("close_price"),
                        volume=latest.get("volume"),
                        effective_price=latest.get("effective_price") or latest.get("price"),
                        session=latest.get("session"),
                        price_policy=latest.get("price_policy_effective"),
                    )
                )
            for row in market_data.get("recent", []):
                recent_quotes.append(
                    RecentQuote(
                        timestamp=_to_iso(row.get("timestamp")),
                        open=row.get("open"),
                        high=row.get("high"),
                        low=row.get("low"),
                        close=row.get("close") or row.get("price") or row.get("effective_price"),
                        volume=row.get("volume"),
                        effective_price=row.get("effective_price") or row.get("price"),
                        session=row.get("session"),
                        price_policy=row.get("price_policy_effective"),
                    )
                )

        # Timeline rows from evaluation timeline (audit trail)
        start_delta = _parse_window(window)
        end_ts = datetime.now(timezone.utc)
        start_ts = end_ts - start_delta if start_delta else None

        timeline_rows: List[Dict[str, Any]] = []
        if hasattr(container, "evaluation_timeline"):
            # Recent evaluation rows (capped to avoid timeout)
            recent_rows = container.evaluation_timeline.list_by_position(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position_id=position_id,
                mode="LIVE",
                start_date=start_ts,
                end_date=end_ts,
                limit=timeline_limit,
            )
            # Always fetch all trade events (BUY/SELL) regardless of time window
            # so they are never excluded by the row limit
            trade_rows = container.evaluation_timeline.list_by_position(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position_id=position_id,
                mode="LIVE",
                start_date=None,
                end_date=end_ts,
                action_filter=["BUY", "SELL"],
                limit=1000,
            )
            # Merge: start with recent rows, add any trade rows not already included
            seen_ids = {r.get("id") for r in recent_rows if r.get("id")}
            extra_trades = [r for r in trade_rows if r.get("id") not in seen_ids]
            timeline_rows = sorted(
                recent_rows + extra_trades,
                key=lambda r: str(r.get("timestamp") or ""),
                reverse=True,
            )

        # Enrich rows: fill null trigger/guardrail thresholds from per-position config.
        if timeline_rows:
            from app.di import container as _container
            _trigger = _container.config.get_trigger_config(position_id)
            _guardrail = _container.config.get_guardrail_config(position_id)
            enrich_trigger_up = float(_trigger.up_threshold_pct) if _trigger else 3.0
            enrich_trigger_dn = float(_trigger.down_threshold_pct) if _trigger else -3.0
            enrich_min_pct = float(_guardrail.min_stock_pct) * 100 if _guardrail else 25.0
            enrich_max_pct = float(_guardrail.max_stock_pct) * 100 if _guardrail else 75.0
            for row in timeline_rows:
                if row.get("trigger_up_threshold") is None:
                    row["trigger_up_threshold"] = enrich_trigger_up
                if row.get("trigger_down_threshold") is None:
                    row["trigger_down_threshold"] = enrich_trigger_dn
                if row.get("guardrail_min_stock_pct") is None:
                    row["guardrail_min_stock_pct"] = enrich_min_pct
                if row.get("guardrail_max_stock_pct") is None:
                    row["guardrail_max_stock_pct"] = enrich_max_pct

        return CockpitResponse(
            position_summary=position_summary,
            baseline_comparison=baseline_comparison,
            allocation_band=allocation_band,
            recent_quotes=recent_quotes,
            timeline_rows=timeline_rows,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error building cockpit: {exc}") from exc
