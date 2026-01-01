# backend/app/routes/orders.py
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header

from app.di import container
from application.dto.orders import (
    CreateOrderRequest,
    CreateOrderResponse,
    FillOrderRequest,
    FillOrderResponse,
)
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.use_cases.execute_order_uc import ExecuteOrderUC
from domain.errors import GuardrailBreach

router = APIRouter(tags=["orders"])


# REMOVED: Legacy order endpoints - Use portfolio-scoped endpoints instead:
# POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders
# GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders


@router.post(
    "/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders",
    response_model=CreateOrderResponse,
)
def submit_order(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    payload: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> CreateOrderResponse:
    uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        idempotency=container.idempotency,
        config_repo=container.config,
        clock=container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
    )
    try:
        return uc.execute(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            request=payload,
            idempotency_key=(idempotency_key or ""),
        )
    except KeyError as e:
        if str(e) == "position_not_found":
            raise HTTPException(status_code=404, detail="position_not_found")
        raise
    except Exception as e:
        # Check if it's a domain exception
        if e.__class__.__name__ == "PositionNotFound":
            raise HTTPException(status_code=404, detail="position_not_found")
        print(f"Unexpected error in submit_order: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/fill", response_model=FillOrderResponse)
def fill_order(order_id: str, payload: FillOrderRequest) -> FillOrderResponse:
    uc = ExecuteOrderUC(
        positions=container.positions,
        orders=container.orders,
        trades=container.trades,
        events=container.events,
        clock=container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
        order_policy_config_provider=container.order_policy_config_provider,
    )
    try:
        return uc.execute(order_id=order_id, request=payload)
    except KeyError:
        # Normalize to HTTP 404 for missing order
        raise HTTPException(404, detail="order_not_found")
    except GuardrailBreach as e:
        # Guardrail violation - return 400 Bad Request
        raise HTTPException(400, detail=f"guardrail_breach: {str(e)}")
    except Exception as e:
        # Log the full error for debugging
        import traceback

        traceback.print_exc()
        raise HTTPException(500, detail=f"Error filling order: {str(e)}")


@router.post(
    "/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders/auto-size"
)
def submit_auto_sized_order(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    current_price: float,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> Dict[str, Any]:
    """Submit an order with automatic sizing based on volatility triggers and guardrails."""

    # First, evaluate the position to get the order proposal
    eval_uc = container.evaluate_position_uc

    try:
        evaluation = eval_uc.evaluate(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            current_price=current_price,
        )
    except KeyError:
        raise HTTPException(404, detail="position_not_found")

    if not evaluation["trigger_detected"]:
        return {
            "position_id": position_id,
            "current_price": current_price,
            "order_submitted": False,
            "reason": "No trigger detected - no order needed",
            "evaluation": evaluation,
        }

    order_proposal = evaluation["order_proposal"]

    # Check if the order is valid
    if not order_proposal["validation"]["valid"]:
        return {
            "position_id": position_id,
            "current_price": current_price,
            "order_submitted": False,
            "reason": "Order validation failed",
            "rejections": order_proposal["validation"]["rejections"],
            "evaluation": evaluation,
        }

    # Create the order using the proposal
    order_request = CreateOrderRequest(
        side=order_proposal["side"],
        qty=order_proposal["trimmed_qty"],
        price=current_price,
    )

    # Submit the order
    submit_uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        idempotency=container.idempotency,
        config_repo=container.config,
        clock=container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
    )

    try:
        order_response = submit_uc.execute(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            request=order_request,
            idempotency_key=(idempotency_key or ""),
        )

        return {
            "position_id": position_id,
            "current_price": current_price,
            "order_submitted": True,
            "order_id": order_response.order_id,
            "order_details": order_response,
            "sizing_details": {
                "raw_qty": order_proposal["raw_qty"],
                "trimmed_qty": order_proposal["trimmed_qty"],
                "notional": order_proposal["notional"],
                "commission": order_proposal["commission"],
                "trimming_reason": order_proposal["trimming_reason"],
                "post_trade_asset_pct": order_proposal["post_trade_asset_pct"],
            },
            "evaluation": evaluation,
        }

    except Exception as e:
        return {
            "position_id": position_id,
            "current_price": current_price,
            "order_submitted": False,
            "reason": f"Order submission failed: {str(e)}",
            "evaluation": evaluation,
        }


@router.post(
    "/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders/auto-size/market"
)
def submit_auto_sized_order_with_market_data(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> Dict[str, Any]:
    """Submit an order with automatic sizing using real-time market data and after-hours support."""

    # First, evaluate the position with market data to get the order proposal
    eval_uc = container.get_evaluate_position_uc()

    try:
        evaluation = eval_uc.evaluate_with_market_data(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
    except KeyError:
        raise HTTPException(404, detail="position_not_found")

    if not evaluation["trigger_detected"]:
        return {
            "position_id": position_id,
            "current_price": evaluation.get("current_price"),
            "order_submitted": False,
            "reason": "No trigger detected - no order needed",
            "evaluation": evaluation,
        }

    order_proposal = evaluation["order_proposal"]

    # Check if the order is valid
    if not order_proposal["validation"]["valid"]:
        return {
            "position_id": position_id,
            "current_price": evaluation.get("current_price"),
            "order_submitted": False,
            "reason": "Order validation failed",
            "rejections": order_proposal["validation"]["rejections"],
            "evaluation": evaluation,
        }

    # Create the order using the proposal
    order_request = CreateOrderRequest(
        side=order_proposal["side"],
        qty=order_proposal["trimmed_qty"],
        price=evaluation["current_price"],
    )

    # Submit the order
    submit_uc = SubmitOrderUC(
        positions=container.positions,
        orders=container.orders,
        events=container.events,
        idempotency=container.idempotency,
        config_repo=container.config,
        clock=container.clock,
        guardrail_config_provider=container.guardrail_config_provider,
    )

    try:
        order_response = submit_uc.execute(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            request=order_request,
            idempotency_key=(idempotency_key or ""),
        )

        return {
            "position_id": position_id,
            "current_price": evaluation["current_price"],
            "order_submitted": True,
            "order_id": order_response.order_id,
            "order_details": order_response,
            "sizing_details": {
                "raw_qty": order_proposal["raw_qty"],
                "trimmed_qty": order_proposal["trimmed_qty"],
                "notional": order_proposal["notional"],
                "commission": order_proposal["commission"],
                "trimming_reason": order_proposal["trimming_reason"],
                "post_trade_asset_pct": order_proposal["post_trade_asset_pct"],
            },
            "market_data": evaluation.get("market_data"),
            "evaluation": evaluation,
        }

    except Exception as e:
        return {
            "position_id": position_id,
            "current_price": evaluation.get("current_price"),
            "order_submitted": False,
            "reason": f"Order submission failed: {str(e)}",
            "evaluation": evaluation,
        }


@router.get("/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders")
def list_orders(
    tenant_id: str, portfolio_id: str, position_id: str, limit: int = 100
) -> Dict[str, Any]:
    if not container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
    ):
        raise HTTPException(404, detail="position_not_found")
    orders = container.orders.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "orders": [asdict(o) for o in orders]}


@router.get("/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/trades")
def list_trades(
    tenant_id: str, portfolio_id: str, position_id: str, limit: int = 100
) -> Dict[str, Any]:
    """List trades for a position, ordered by execution time (newest first)."""
    if not container.positions.get(
        tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
    ):
        raise HTTPException(404, detail="position_not_found")
    trades = container.trades.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "trades": [asdict(t) for t in trades]}


@router.get("/orders/{order_id}/trades")
def list_trades_for_order(order_id: str) -> Dict[str, Any]:
    """List trades for a specific order."""
    if not container.orders.get(order_id):
        raise HTTPException(404, detail="order_not_found")
    trades = container.trades.list_for_order(order_id)
    return {"order_id": order_id, "trades": [asdict(t) for t in trades]}
