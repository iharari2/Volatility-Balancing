#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import uuid
from typing import Any, Dict, List

import requests


def _request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    response = requests.request(method, url, timeout=10, **kwargs)
    if not response.ok:
        raise RuntimeError(f"{method} {url} failed: {response.status_code} {response.text}")
    return response.json()


def _create_portfolio(base_url: str, tenant_id: str) -> str:
    payload = {
        "name": f"Gate1 Tick Smoke {uuid.uuid4().hex[:8]}",
        "description": "Gate1 deterministic tick verification",
        "type": "LIVE",
        "template": "DEFAULT",
        "hours_policy": "OPEN_PLUS_AFTER_HOURS",
    }
    result = _request("POST", f"{base_url}/v1/tenants/{tenant_id}/portfolios", json=payload)
    return result["portfolio_id"]


def _create_position(
    base_url: str,
    tenant_id: str,
    portfolio_id: str,
    ticker: str,
    qty: float,
    cash: float,
    anchor_price: float,
) -> str:
    payload = {
        "asset": ticker,
        "qty": qty,
        "avg_cost": None,
        "anchor_price": anchor_price,
        "starting_cash": {"currency": "USD", "amount": cash},
    }
    result = _request(
        "POST",
        f"{base_url}/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions",
        json=payload,
    )
    return result["position_id"]


def _trigger_direction(action: str) -> str:
    if action == "BUY":
        return "DOWN"
    if action == "SELL":
        return "UP"
    return "NONE"


def _print_tick_summary(rows: List[Dict[str, Any]]) -> None:
    print("Tick Summary")
    for row in rows:
        print(
            f"{row['tick']:>2} price={row['price']:.2f} action={row['action']:<4} "
            f"trigger={row['trigger_direction']:<4} order={row['order']} trade={row['trade']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate 1 deterministic tick smoke test")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--tenant-id", default="default")
    parser.add_argument("--portfolio-id")
    parser.add_argument("--position-id")
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--qty", type=float, default=10.0)
    parser.add_argument("--cash", type=float, default=10000.0)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    tenant_id = args.tenant_id

    position_id = args.position_id
    portfolio_id = args.portfolio_id

    if not position_id:
        if not portfolio_id:
            portfolio_id = _create_portfolio(base_url, tenant_id)

        price_quote = _request("GET", f"{base_url}/v1/market/price/{args.ticker}")
        anchor_price = float(price_quote["price"])
        position_id = _create_position(
            base_url=base_url,
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            ticker=args.ticker,
            qty=args.qty,
            cash=args.cash,
            anchor_price=anchor_price,
        )

    tick_rows: List[Dict[str, Any]] = []
    for tick in range(1, 11):
        result = _request("POST", f"{base_url}/v1/positions/{position_id}/tick")
        snapshot = result["position_snapshot"]
        cycle = result["cycle_result"]
        action = cycle["action"]
        tick_rows.append(
            {
                "tick": tick,
                "price": snapshot["current_price"],
                "action": action,
                "trigger_direction": _trigger_direction(action),
                "order": "yes" if cycle["order_id"] else "no",
                "trade": "yes" if cycle["trade_id"] else "no",
            }
        )

    _print_tick_summary(tick_rows)

    timeline = _request(
        "GET",
        f"{base_url}/v1/positions/{position_id}/timeline",
        params={"limit": 200},
    )
    counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "SKIP": 0}
    for row in timeline:
        action = row.get("action", "HOLD")
        counts[action] = counts.get(action, 0) + 1

    print("")
    print(f"Timeline Counts BUY={counts.get('BUY', 0)} SELL={counts.get('SELL', 0)} HOLD={counts.get('HOLD', 0)}")
    print("Last 5 Events")
    for row in timeline[:5]:
        print(
            f"{row.get('timestamp')} action={row.get('action')} "
            f"trigger={row.get('trigger_direction')} price={row.get('current_price')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
