#!/usr/bin/env python3
"""
Parameter Optimization Results Viewer
Shows detailed results from the optimization system
"""

import requests
import json
from typing import List, Dict, Any


def get_optimization_results(config_id: str) -> List[Dict[str, Any]]:
    """Get optimization results from the API"""
    try:
        response = requests.get(
            f"http://localhost:8000/v1/optimization/configs/{config_id}/results"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching results: {e}")
        return []


def get_optimization_config(config_id: str) -> Dict[str, Any]:
    """Get optimization configuration from the API"""
    try:
        response = requests.get(f"http://localhost:8000/v1/optimization/configs/{config_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching config: {e}")
        return {}


def display_results_summary(results: List[Dict[str, Any]]):
    """Display a summary of optimization results"""
    if not results:
        print("❌ No results found")
        return

    print("🔍 OPTIMIZATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Results: {len(results)}")

    # Calculate statistics
    sharpe_ratios = [r["metrics"]["sharpe_ratio"] for r in results]
    total_returns = [r["metrics"]["total_return"] for r in results]
    max_drawdowns = [r["metrics"]["max_drawdown"] for r in results]

    print(f"Sharpe Ratio Range: {min(sharpe_ratios):.3f} to {max(sharpe_ratios):.3f}")
    print(f"Total Return Range: {min(total_returns):.3f} to {max(total_returns):.3f}")
    print(f"Max Drawdown Range: {min(max_drawdowns):.3f} to {max(max_drawdowns):.3f}")
    print()


def display_top_results(results: List[Dict[str, Any]], top_n: int = 5):
    """Display top N results by Sharpe ratio"""
    if not results:
        return

    # Sort by Sharpe ratio (descending)
    sorted_results = sorted(results, key=lambda x: x["metrics"]["sharpe_ratio"], reverse=True)

    print(f"🏆 TOP {top_n} RESULTS BY SHARPE RATIO")
    print("=" * 60)

    for i, result in enumerate(sorted_results[:top_n], 1):
        metrics = result["metrics"]
        params = result["parameter_combination"]

        print(f"Rank #{i}")
        print(f"  📊 Performance Metrics:")
        print(f"     Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"     Total Return: {metrics['total_return']:.3f}")
        print(f"     Max Drawdown: {metrics['max_drawdown']:.3f}")
        print(f"     Volatility: {metrics['volatility']:.3f}")
        print(f"     Win Rate: {metrics['win_rate']:.3f}")
        print(f"     Trade Count: {metrics['trade_count']}")
        print(f"  ⚙️  Parameters:")
        for param, value in params.items():
            print(f"     {param}: {value}")
        print()


def display_parameter_analysis(results: List[Dict[str, Any]]):
    """Analyze parameter impact on performance"""
    if not results:
        return

    print("📈 PARAMETER IMPACT ANALYSIS")
    print("=" * 60)

    # Group by parameters to see patterns
    param_groups = {}
    for result in results:
        params = result["parameter_combination"]
        sharpe = result["metrics"]["sharpe_ratio"]

        # Create a key for grouping
        key = tuple(sorted(params.items()))
        if key not in param_groups:
            param_groups[key] = []
        param_groups[key].append(sharpe)

    # Show parameter combinations and their average performance
    print("Parameter Combinations vs Average Sharpe Ratio:")
    print("-" * 50)

    for params, sharpe_ratios in sorted(
        param_groups.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True
    ):
        avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios)
        param_str = ", ".join([f"{k}={v}" for k, v in params])
        print(f"  {param_str:<30} → {avg_sharpe:.3f}")


def display_heatmap_data(config_id: str):
    """Display heatmap data for visualization"""
    try:
        response = requests.get(
            f"http://localhost:8000/v1/optimization/configs/{config_id}/heatmap?x_parameter=trigger_threshold_pct&y_parameter=rebalance_ratio&metric=sharpe_ratio"
        )
        response.raise_for_status()
        heatmap_data = response.json()

        print("🗺️  HEATMAP DATA")
        print("=" * 60)
        print(f"X Parameter: {heatmap_data['x_parameter']}")
        print(f"Y Parameter: {heatmap_data['y_parameter']}")
        print(f"Metric: {heatmap_data['metric']}")
        print(
            f"Value Range: {heatmap_data['statistics']['min']:.3f} to {heatmap_data['statistics']['max']:.3f}"
        )
        print()

        # Show sample heatmap cells
        print("Sample Heatmap Cells:")
        print("-" * 30)
        for i, cell in enumerate(heatmap_data["cells"][:10]):  # Show first 10 cells
            print(
                f"  X={cell['x_value']:.3f}, Y={cell['y_value']:.3f} → {cell['metric_value']:.3f}"
            )

    except Exception as e:
        print(f"❌ Error fetching heatmap data: {e}")


def main():
    """Main function to display optimization results"""
    # Use the config ID from the demo
    config_id = "037c6065-d857-47f1-b527-fec0d8e938b3"

    print("🚀 PARAMETER OPTIMIZATION RESULTS VIEWER")
    print("=" * 60)
    print(f"Configuration ID: {config_id}")
    print()

    # Get configuration details
    config = get_optimization_config(config_id)
    if config:
        print("📋 CONFIGURATION DETAILS")
        print("-" * 30)
        print(f"Name: {config.get('name', 'N/A')}")
        print(f"Ticker: {config.get('ticker', 'N/A')}")
        print(f"Status: {config.get('status', 'N/A')}")
        print(f"Total Combinations: {config.get('total_combinations', 'N/A')}")
        print()

    # Get and display results
    results = get_optimization_results(config_id)

    if results:
        display_results_summary(results)
        display_top_results(results, top_n=5)
        display_parameter_analysis(results)
        display_heatmap_data(config_id)

        print("💡 HOW TO INTERPRET THESE RESULTS:")
        print("-" * 40)
        print("• Sharpe Ratio: Higher is better (risk-adjusted returns)")
        print("• Total Return: Higher is better (absolute returns)")
        print("• Max Drawdown: Closer to 0 is better (less risk)")
        print("• Win Rate: Higher is better (more profitable trades)")
        print("• Trade Count: Shows how active the strategy is")
        print()
        print("🎯 BEST STRATEGY:")
        best = max(results, key=lambda x: x["metrics"]["sharpe_ratio"])
        print(f"   Use parameters: {best['parameter_combination']}")
        print(f"   Expected Sharpe Ratio: {best['metrics']['sharpe_ratio']:.3f}")
    else:
        print("❌ No results found. Make sure the optimization has completed.")


if __name__ == "__main__":
    main()
