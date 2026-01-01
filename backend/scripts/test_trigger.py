#!/usr/bin/env python3
"""
Test if triggers are configured correctly and would fire.

This script:
1. Gets position and current price
2. Calculates price change from anchor
3. Shows what threshold is needed
4. Tests evaluation to see if trigger would fire
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.di import container
from application.use_cases.evaluate_position_uc import EvaluatePositionUC


def test_trigger(position_id):
    """Test trigger configuration for a position."""
    print("=" * 80)
    print(f"TESTING TRIGGERS FOR {position_id}")
    print("=" * 80)

    # Find position
    position = None
    tenant_id = "default"
    portfolio_id = None

    portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
    for p in portfolios:
        pos = container.positions.get(tenant_id, p.id, position_id)
        if pos:
            position = pos
            portfolio_id = p.id
            break

    if not position:
        print(f"❌ Position {position_id} not found")
        return

    print(f"\n✅ Position: {position.asset_symbol}")
    print(f"   Anchor Price: ${position.anchor_price:.2f}")
    print(f"   Current Qty: {position.qty:.4f}")
    print(f"   Current Cash: ${position.cash:.2f}")

    # Get current price
    price_data = container.market_data.get_price(position.asset_symbol, force_refresh=True)
    if not price_data or not price_data.price:
        print("❌ Could not get price")
        return

    current_price = float(price_data.price)
    anchor_price = float(position.anchor_price) if position.anchor_price else 0

    print(f"   Current Price: ${current_price:.2f}")

    # Calculate price change
    price_change = current_price - anchor_price
    price_change_pct = (price_change / anchor_price) * 100 if anchor_price > 0 else 0

    print("\n📊 Price Analysis:")
    print(f"   Price Change: ${price_change:+.2f} ({price_change_pct:+.2f}%)")

    # Get trigger config
    if container.trigger_config_provider:
        trigger_config = container.trigger_config_provider(tenant_id, portfolio_id, position_id)
        up_threshold = float(trigger_config.up_threshold_pct) * 100
        down_threshold = float(trigger_config.down_threshold_pct) * 100
    else:
        # Fallback to order_policy
        if position.order_policy:
            up_threshold = float(position.order_policy.trigger_threshold_pct) * 100
            down_threshold = float(position.order_policy.trigger_threshold_pct) * 100
        else:
            up_threshold = 3.0  # Default
            down_threshold = 3.0

    print("\n⚙️  Trigger Configuration:")
    print(f"   Up Threshold: {up_threshold:.2f}% (SELL when price goes up)")
    print(f"   Down Threshold: {down_threshold:.2f}% (BUY when price goes down)")

    print("\n🔍 Trigger Status:")
    if price_change_pct <= -down_threshold:
        print(
            f"   ✅ BUY trigger SHOULD FIRE (down {abs(price_change_pct):.2f}% >= {down_threshold:.2f}%)"
        )
    elif price_change_pct >= up_threshold:
        print(f"   ✅ SELL trigger SHOULD FIRE (up {price_change_pct:.2f}% >= {up_threshold:.2f}%)")
    else:
        print(
            f"   ⚠️  NO TRIGGER (change {abs(price_change_pct):.2f}% < threshold {min(up_threshold, down_threshold):.2f}%)"
        )
        print(
            f"   → Price needs to move {min(up_threshold, down_threshold) - abs(price_change_pct):.2f}% more to trigger"
        )

    # Test evaluation
    print("\n🧪 Testing Evaluation...")
    eval_uc = EvaluatePositionUC(
        positions=container.positions,
        events=container.events,
        market_data=container.market_data,
        clock=container.clock,
        portfolio_repo=container.portfolio_repo,
    )

    try:
        result = eval_uc.evaluate(tenant_id, portfolio_id, position_id, current_price)

        print(f"   Trigger Detected: {result.get('trigger_detected', False)}")
        print(f"   Trigger Type: {result.get('trigger_type')}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')}")

        order_proposal = result.get("order_proposal")
        if order_proposal:
            print("\n   ✅ Order Proposal Generated:")
            print(f"      Side: {order_proposal.get('side')}")
            print(f"      Qty: {order_proposal.get('trimmed_qty', 0)}")
            validation = order_proposal.get("validation", {})
            print(f"      Valid: {validation.get('valid', False)}")
            if not validation.get("valid"):
                print(f"      Rejections: {validation.get('rejections', [])}")
        else:
            print("\n   ⚠️  No order proposal")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_trigger.py <position_id>")
        sys.exit(1)

    test_trigger(sys.argv[1])
