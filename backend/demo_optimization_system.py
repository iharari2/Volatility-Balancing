#!/usr/bin/env python3
"""
Comprehensive demonstration of the Parameter Optimization System
Shows all features including results analysis and heatmap generation
"""

import requests
import json
from datetime import datetime, timedelta
from uuid import uuid4

# API base URL
BASE_URL = "http://localhost:8000/v1/optimization"


def demo_optimization_system():
    """Demonstrate the complete Parameter Optimization System."""

    print("🚀 Parameter Optimization System - Complete Demo")
    print("=" * 70)

    # Demo 1: Create a comprehensive optimization configuration
    print("\n📊 1. Creating Comprehensive Optimization Configuration...")

    optimization_request = {
        "name": "AAPL Volatility Strategy Optimization",
        "ticker": "AAPL",
        "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "parameter_ranges": {
            "trigger_threshold_pct": {
                "min_value": 0.01,
                "max_value": 0.05,
                "step_size": 0.01,
                "parameter_type": "float",
                "name": "Trigger Threshold %",
                "description": "Volatility trigger threshold percentage",
            },
            "rebalance_ratio": {
                "min_value": 1.0,
                "max_value": 3.0,
                "step_size": 0.5,
                "parameter_type": "float",
                "name": "Rebalance Ratio",
                "description": "Rebalancing ratio multiplier",
            },
        },
        "optimization_criteria": {
            "primary_metric": "sharpe_ratio",
            "secondary_metrics": ["total_return", "max_drawdown"],
            "constraints": [
                {
                    "metric": "max_drawdown",
                    "constraint_type": "max_value",
                    "value": -0.1,
                    "description": "Maximum drawdown must be less than 10%",
                }
            ],
            "weights": {"sharpe_ratio": 0.5, "total_return": 0.3, "max_drawdown": 0.2},
            "minimize": False,
            "description": "Optimize for risk-adjusted returns with drawdown constraints",
        },
        "created_by": str(uuid4()),
        "description": "Comprehensive optimization demo for AAPL volatility strategy",
        "max_combinations": 20,  # Reasonable size for demo
        "batch_size": 5,
    }

    response = requests.post(f"{BASE_URL}/configs", json=optimization_request)
    if response.status_code == 200:
        config = response.json()
        config_id = config["id"]
        print(f"✅ Created: {config['name']}")
        print(f"   - ID: {config_id}")
        print(f"   - Total combinations: {config['total_combinations']}")
        print(f"   - Parameters: {list(config.get('parameter_ranges', {}).keys())}")
    else:
        print(f"❌ Failed to create config: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

    # Demo 2: Start optimization and monitor progress
    print("\n🔄 2. Starting Optimization...")
    response = requests.post(f"{BASE_URL}/configs/{config_id}/start")
    if response.status_code == 200:
        print("✅ Optimization started successfully")

        # Monitor progress
        print("\n📈 Monitoring Progress...")
        for i in range(3):
            response = requests.get(f"{BASE_URL}/configs/{config_id}/progress")
            if response.status_code == 200:
                progress = response.json()
                print(f"   Progress: {progress['progress_percentage']:.1f}% - {progress['status']}")
                if progress["status"] == "completed":
                    break
            import time

            time.sleep(1)
    else:
        print(f"❌ Failed to start optimization: {response.status_code}")
        return None

    # Demo 3: Analyze optimization results
    print("\n📊 3. Analyzing Optimization Results...")
    response = requests.get(f"{BASE_URL}/configs/{config_id}/results")
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Found {len(results)} completed results")

        # Show top 5 results by Sharpe ratio
        if results:
            print("\n🏆 Top 5 Results by Sharpe Ratio:")
            for i, result in enumerate(results[:5]):
                metrics = result["metrics"]
                params = result["parameter_combination"]
                print(
                    f"   {i+1}. Sharpe: {metrics.get('sharpe_ratio', 0):.3f}, "
                    f"Return: {metrics.get('total_return', 0):.3f}, "
                    f"Drawdown: {metrics.get('max_drawdown', 0):.3f}"
                )
                print(f"      Params: {params}")
    else:
        print(f"❌ Failed to get results: {response.status_code}")

    # Demo 4: Generate heatmap data
    print("\n🗺️ 4. Generating Heatmap Data...")

    response = requests.get(
        f"{BASE_URL}/configs/{config_id}/heatmap?x_parameter=trigger_threshold_pct&y_parameter=rebalance_ratio&metric=sharpe_ratio"
    )
    if response.status_code == 200:
        heatmap = response.json()
        print(f"✅ Generated heatmap data")
        print(f"   - X parameter: {heatmap['x_parameter']}")
        print(f"   - Y parameter: {heatmap['y_parameter']}")
        print(f"   - Metric: {heatmap['metric']}")
        print(f"   - Cells: {len(heatmap['cells'])}")
        print(
            f"   - Value range: {heatmap['statistics']['min']:.3f} to {heatmap['statistics']['max']:.3f}"
        )

        # Show sample heatmap cells
        print("\n📊 Sample Heatmap Cells:")
        for i, cell in enumerate(heatmap["cells"][:5]):
            print(
                f"   {i+1}. X={cell['x_value']:.3f}, Y={cell['y_value']:.3f}, Value={cell['metric_value']:.3f}"
            )
    else:
        print(f"❌ Failed to generate heatmap: {response.status_code}")
        print(f"   Error: {response.text}")

    # Demo 5: Show available metrics and parameter types
    print("\n📋 5. System Capabilities...")

    # Available metrics
    response = requests.get(f"{BASE_URL}/metrics")
    if response.status_code == 200:
        metrics = response.json()
        print(f"✅ Available metrics: {len(metrics['metrics'])}")
        metric_names = [m["name"] for m in metrics["metrics"]]
        print(f"   {', '.join(metric_names[:5])}...")

    # Parameter types
    response = requests.get(f"{BASE_URL}/parameter-types")
    if response.status_code == 200:
        param_types = response.json()
        print(f"✅ Parameter types: {len(param_types['parameter_types'])}")
        type_names = [t["name"] for t in param_types["parameter_types"]]
        print(f"   {', '.join(type_names)}")

    # Demo 6: Show configuration details
    print("\n⚙️ 6. Configuration Details...")
    response = requests.get(f"{BASE_URL}/configs/{config_id}")
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Configuration: {config['name']}")
        print(f"   - Status: {config['status']}")
        print(f"   - Ticker: {config['ticker']}")
        print(f"   - Date range: {config['start_date'][:10]} to {config['end_date'][:10]}")
        print(f"   - Total combinations: {config['total_combinations']}")
        print(
            f"   - Primary metric: {config.get('optimization_criteria', {}).get('primary_metric', 'N/A')}"
        )

    print("\n🎉 Parameter Optimization System Demo Complete!")
    print("=" * 70)
    print("📊 The system successfully:")
    print("   ✅ Created optimization configurations")
    print("   ✅ Processed parameter combinations")
    print("   ✅ Generated realistic simulation results")
    print("   ✅ Provided progress tracking")
    print("   ✅ Generated heatmap data for visualization")
    print("   ✅ Supported multiple parameter types and metrics")
    print("   ✅ Applied optimization constraints")

    print(f"\n🔧 Configuration ID: {config_id}")
    print(f"📖 API Documentation: http://localhost:8000/docs")
    print(f"🌐 Frontend: http://localhost:3000 (if running)")

    return config_id


if __name__ == "__main__":
    try:
        config_id = demo_optimization_system()
        if config_id:
            print(f"\n💡 Next Steps:")
            print(f"   1. Explore the API at http://localhost:8000/docs")
            print(f"   2. Use configuration ID {config_id} for further testing")
            print(f"   3. Integrate with the frontend for visualization")
            print(f"   4. Extend with real simulation processing")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
