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

        # Fetch portfolio config once (not per position)
        cfg = None
        try:
            cfg = portfolio_service._portfolio_config_repo.get(
                tenant_id=tenant_id, portfolio_id=portfolio_id
            )
        except Exception:
            pass

        results: List[PositionSummaryItem] = []
        for position in positions:
            # Use stored price — no yfinance calls on the list endpoint
            price = position.anchor_price or position.avg_cost

            stock_value = (price or 0.0) * position.qty
            total_value = position.cash + stock_value
            stock_pct = (stock_value / total_value * 100) if total_value > 0 else None

            # Guardrail / trigger config (from DB config, no market call)
            guardrail_min_pct: Optional[float] = None
            guardrail_max_pct: Optional[float] = None
            trigger_up_pct: Optional[float] = None
            trigger_down_pct: Optional[float] = None
            try:
                pos_gc = container.config.get_guardrail_config(position.id)
                if pos_gc:
                    guardrail_min_pct = float(pos_gc.min_stock_pct) * 100
                    guardrail_max_pct = float(pos_gc.max_stock_pct) * 100
                elif cfg:
                    guardrail_min_pct = cfg.min_stock_pct
                    guardrail_max_pct = cfg.max_stock_pct
                if cfg:
                    trigger_up_pct = cfg.trigger_up_pct
                    trigger_down_pct = cfg.trigger_down_pct
            except Exception:
                pass

            # Trading status from DB
            status: Optional[str] = "RUNNING"
            try:
                if hasattr(portfolio_service._positions_repo, "_sf"):
                    from infrastructure.persistence.sql.models import PositionModel
                    with portfolio_service._positions_repo._sf() as session:
                        model = session.get(PositionModel, position.id)
                        if model and model.status:
                            status = model.status
            except Exception:
                pass

            # Last robot action from evaluation timeline (1 row, DB-only)
            last_action_obj: Optional[LastAction] = None
            try:
                if hasattr(container, "evaluation_timeline"):
                    rows = container.evaluation_timeline.list_by_position(
                        tenant_id=tenant_id,
                        portfolio_id=portfolio_id,
                        position_id=position.id,
                        mode="LIVE",
                        start_date=None,
                        end_date=None,
                        action_filter=["BUY", "SELL"],
                        limit=1,
                    )
                    if rows:
                        r = rows[0]
                        last_action_obj = LastAction(
                            action=r.get("action"),
                            timestamp=_to_iso(r.get("timestamp")),
                            reason=r.get("reason") or r.get("action_reason"),
                        )
            except Exception:
                pass

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

        # Enrich rows: fill null trigger/guardrail thresholds from current portfolio config
        # so the frontend can always compute dollar values from per-row anchor + total_value.
        try:
            cfg = portfolio_service._portfolio_config_repo.get(
                tenant_id=tenant_id, portfolio_id=portfolio_id
            )
        except Exception:
            cfg = None

        if cfg and timeline_rows:
            cfg_trigger_up = getattr(cfg, "trigger_up_pct", None)
            cfg_trigger_dn = getattr(cfg, "trigger_down_pct", None)
            cfg_min_pct = float(getattr(cfg, "min_stock_pct", None) or 0)
            cfg_max_pct = float(getattr(cfg, "max_stock_pct", None) or 0)
            for row in timeline_rows:
                if row.get("trigger_up_threshold") is None and cfg_trigger_up is not None:
                    row["trigger_up_threshold"] = float(cfg_trigger_up)
                if row.get("trigger_down_threshold") is None and cfg_trigger_dn is not None:
                    row["trigger_down_threshold"] = float(cfg_trigger_dn)
                if row.get("guardrail_min_stock_pct") is None and cfg_min_pct:
                    row["guardrail_min_stock_pct"] = cfg_min_pct
                if row.get("guardrail_max_stock_pct") is None and cfg_max_pct:
                    row["guardrail_max_stock_pct"] = cfg_max_pct

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
