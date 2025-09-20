#!/usr/bin/env python3
"""
Generate trigger analysis table for ZIM stock over a period
This bypasses the SimulationResult issue by creating analysis directly
"""
import requests
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd


def generate_trigger_analysis(ticker="ZIM", days=30):
    """Generate a trigger analysis table for a stock over a period"""

    # Get historical data
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    print(f"Generating trigger analysis for {ticker} from {start_date.date()} to {end_date.date()}")

    # Fetch data using yfinance directly with minute-by-minute data
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date, interval="1m")

    if hist.empty:
        print("No historical data found")
        return []

    # Simulation parameters
    trigger_threshold_pct = 0.03  # 3%
    initial_cash = 10000

    # Simulate the trading logic
    trigger_analysis = []
    position_qty = 0
    position_cash = initial_cash
    anchor_price = None

    for date, row in hist.iterrows():
        current_price = row["Close"]
        open_price = row["Open"]
        high_price = row["High"]
        low_price = row["Low"]
        volume = row["Volume"]

        # Set initial anchor price
        if anchor_price is None:
            anchor_price = current_price

        # Calculate price change from anchor
        price_change_pct = ((current_price / anchor_price) - 1) * 100 if anchor_price else 0

        # Check if trigger threshold is met
        triggered = abs(price_change_pct) >= (trigger_threshold_pct * 100)

        # Determine side and quantity
        side = None
        qty = 0
        executed = False
        reason = f"Price change {price_change_pct:.2f}% below threshold {trigger_threshold_pct * 100:.2f}%"
        execution_error = None

        if triggered:
            if price_change_pct > 0:
                # Price went up, consider selling
                side = "SELL"
                if position_qty > 0:
                    # Calculate sell quantity (simplified)
                    total_value = position_cash + (position_qty * current_price)
                    qty = (
                        abs(price_change_pct) / 100 * total_value / current_price * 0.5
                    )  # rebalance_ratio = 0.5
                    qty = min(qty, position_qty)  # Can't sell more than we have

                    if qty >= 1:  # Minimum 1 share
                        executed = True
                        position_qty -= qty
                        position_cash += qty * current_price
                        anchor_price = current_price  # Update anchor
                        reason = "Sell trigger executed"
                    else:
                        reason = "Sell trigger but insufficient quantity"
                        execution_error = "insufficient_qty"
                else:
                    reason = "Sell trigger but no shares to sell"
                    execution_error = "no_shares"
            else:
                # Price went down, consider buying
                side = "BUY"
                if position_cash > 100:  # Minimum $100 to trade
                    # Calculate buy quantity (simplified)
                    total_value = position_cash + (position_qty * current_price)
                    qty = (
                        abs(price_change_pct) / 100 * total_value / current_price * 0.5
                    )  # rebalance_ratio = 0.5
                    max_qty = position_cash / current_price
                    qty = min(qty, max_qty)

                    if qty >= 1 and qty * current_price >= 100:  # Minimum 1 share and $100
                        executed = True
                        position_qty += qty
                        position_cash -= qty * current_price
                        anchor_price = current_price  # Update anchor
                        reason = "Buy trigger executed"
                    else:
                        reason = "Buy trigger but insufficient cash"
                        execution_error = "insufficient_cash"
                else:
                    reason = "Buy trigger but insufficient cash"
                    execution_error = "insufficient_cash"

        # Add to analysis (convert numpy types to native Python types for JSON serialization)
        trigger_analysis.append(
            {
                "timestamp": date.strftime("%Y-%m-%d %H:%M:%S"),  # Use actual time
                "date": date.strftime("%Y-%m-%d"),
                "time": date.strftime("%H:%M:%S"),
                "price": float(current_price),
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "volume": int(volume),
                "anchor_price": float(anchor_price),
                "price_change_pct": float(price_change_pct),
                "trigger_threshold": float(trigger_threshold_pct * 100),
                "triggered": bool(triggered),
                "side": side,
                "qty": float(qty),
                "reason": str(reason),
                "executed": bool(executed),
                "execution_error": execution_error,
                "cash_after": float(position_cash),
                "shares_after": float(position_qty),
                "dividend": 0.0,  # Placeholder for dividend data
            }
        )

    return trigger_analysis


def print_trigger_table(trigger_analysis):
    """Print trigger analysis as a formatted table"""

    if not trigger_analysis:
        print("No trigger analysis data")
        return

    # Filter to show only significant events
    significant_events = [
        t
        for t in trigger_analysis
        if t["triggered"] or abs(t["price_change_pct"]) >= t["trigger_threshold"] * 0.5
    ]

    print(f"\n{'='*200}")
    print(f"TRIGGER ANALYSIS TABLE")
    print(f"{'='*200}")
    print(
        f"Showing {len(significant_events)} significant events out of {len(trigger_analysis)} total evaluations"
    )
    print(f"{'='*200}")

    # Table headers - wider format with separate OHLC columns and anchor price
    print(
        f"{'Date':<12} {'Time':<8} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8} {'Anchor':<8} {'Vol':<8} {'Change%':<8} {'Status':<12} {'Side':<6} {'Qty':<8} {'Cash':<10} {'Shares':<8} {'Asset%':<8} {'Dividend':<8} {'Reason':<50}"
    )
    print(f"{'-'*260}")

    # Table rows
    for trigger in significant_events:
        date_str = trigger["date"]  # Just the date part
        time_str = trigger["time"]  # Time part

        # Separate OHLC columns
        open_str = f"${trigger['open']:.2f}"
        high_str = f"${trigger['high']:.2f}"
        low_str = f"${trigger['low']:.2f}"
        close_str = f"${trigger['price']:.2f}"
        anchor_str = f"${trigger['anchor_price']:.2f}"
        vol_str = f"{trigger['volume']:,}"

        change_str = f"{trigger['price_change_pct']:+.2f}%"

        if trigger["executed"]:
            status = "✅ Executed"
        elif trigger["triggered"] and not trigger["executed"]:
            status = "❌ Failed"
        elif abs(trigger["price_change_pct"]) >= trigger["trigger_threshold"]:
            status = "⚠️  Near"
        else:
            status = "⭕ No Trigger"

        side_str = trigger["side"] if trigger["side"] else "-"
        qty_str = f"{trigger['qty']:.1f}" if trigger["qty"] > 0 else "-"

        # Position details
        cash_str = f"${trigger['cash_after']:,.0f}"
        shares_str = f"{trigger['shares_after']:.0f}"

        # Calculate asset percentage
        total_value = trigger["cash_after"] + (trigger["shares_after"] * trigger["price"])
        asset_pct = (
            (trigger["shares_after"] * trigger["price"] / total_value * 100)
            if total_value > 0
            else 0
        )
        asset_pct_str = f"{asset_pct:.1f}%"

        # Dividend
        dividend_str = f"${trigger['dividend']:.2f}"

        reason_str = (
            trigger["reason"][:48] + "..." if len(trigger["reason"]) > 50 else trigger["reason"]
        )

        print(
            f"{date_str:<12} {time_str:<8} {open_str:<8} {high_str:<8} {low_str:<8} {close_str:<8} {anchor_str:<8} {vol_str:<8} {change_str:<8} {status:<12} {side_str:<6} {qty_str:<8} {cash_str:<10} {shares_str:<8} {asset_pct_str:<8} {dividend_str:<8} {reason_str:<50}"
        )

    # Summary statistics
    triggered_count = sum(1 for t in trigger_analysis if t["triggered"])
    executed_count = sum(1 for t in trigger_analysis if t["executed"])

    print(f"{'-'*200}")
    print(
        f"SUMMARY: {triggered_count} triggered, {executed_count} executed out of {len(trigger_analysis)} total evaluations"
    )
    print(f"{'='*200}")


if __name__ == "__main__":
    # Generate analysis
    analysis = generate_trigger_analysis("AAPL", 3)  # 3 days to get 1m data

    # Print table
    print_trigger_table(analysis)

    # Save to JSON for frontend use
    import json

    with open("trigger_analysis_aapl.json", "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\nTrigger analysis saved to trigger_analysis_aapl.json")
