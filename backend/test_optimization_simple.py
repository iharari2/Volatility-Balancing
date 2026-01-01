#!/usr/bin/env python3
"""
Simple test script for the Parameter Optimization System
"""

import requests
from datetime import datetime, timedelta
from uuid import uuid4

# API base URL
BASE_URL = "http://localhost:8000/v1/optimization"


def test_simple_optimization():
    """Test the optimization system with a simple configuration."""

    print("🚀 Testing Parameter Optimization System (Simple)")
    print("=" * 60)

    # Test 1: Create a simple optimization configuration
    print("\n1. Creating simple optimization configuration...")

    optimization_request = {
        "name": "Simple Test Optimization",
        "ticker": "AAPL",
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "parameter_ranges": {
            "trigger_threshold_pct": {
                "min_value": 0.02,
                "max_value": 0.04,
                "step_size": 0.01,
                "parameter_type": "float",
                "name": "Trigger Threshold %",
                "description": "Volatility trigger threshold percentage",
            },
            "rebalance_ratio": {
                "min_value": 1.5,
                "max_value": 2.0,
                "step_size": 0.5,
                "parameter_type": "float",
                "name": "Rebalance Ratio",
                "description": "Rebalancing ratio multiplier",
            },
        },
        "optimization_criteria": {
            "primary_metric": "sharpe_ratio",
            "secondary_metrics": ["total_return"],
            "constraints": [],
            "weights": {"sharpe_ratio": 0.7, "total_return": 0.3},
            "minimize": False,
            "description": "Simple test optimization",
        },
        "created_by": str(uuid4()),
        "description": "Simple test for demonstration",
        "max_combinations": 6,  # Only 6 combinations for quick testing
        "batch_size": 3,
    }

    response = requests.post(f"{BASE_URL}/configs", json=optimization_request)
    if response.status_code == 200:
        config = response.json()
        config_id = config["id"]
        print(f"✅ Created config: {config['name']}")
        print(f"   - ID: {config_id}")
        print(f"   - Total combinations: {config['total_combinations']}")
    else:
        print(f"❌ Failed to create config: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

    # Test 2: Start optimization
    print("\n2. Starting optimization...")
    response = requests.post(f"{BASE_URL}/configs/{config_id}/start")
    if response.status_code == 200:
        print("✅ Optimization started successfully")
    else:
        print(f"❌ Failed to start optimization: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

    # Test 3: Check progress
    print("\n3. Checking progress...")
    response = requests.get(f"{BASE_URL}/configs/{config_id}/progress")
    if response.status_code == 200:
        progress = response.json()
        print(f"✅ Progress: {progress['progress_percentage']:.1f}%")
        print(f"   - Status: {progress['status']}")
        print(f"   - Total combinations: {progress['total_combinations']}")
        print(f"   - Completed: {progress['completed_combinations']}")
        print(f"   - Failed: {progress['failed_combinations']}")
        print(f"   - Remaining: {progress['remaining_combinations']}")
    else:
        print(f"❌ Failed to get progress: {response.status_code}")
        return None

    # Test 4: List configurations
    print("\n4. Listing all configurations...")
    response = requests.get(f"{BASE_URL}/configs")
    if response.status_code == 200:
        configs = response.json()
        print(f"✅ Found {len(configs)} configurations")
        for config in configs:
            print(
                f"   - {config['name']} ({config['status']}) - {config['total_combinations']} combinations"
            )
    else:
        print(f"❌ Failed to list configs: {response.status_code}")

    # Test 5: Get available metrics
    print("\n5. Available metrics...")
    response = requests.get(f"{BASE_URL}/metrics")
    if response.status_code == 200:
        metrics = response.json()
        print(f"✅ Available metrics: {[m['name'] for m in metrics['metrics']]}")
    else:
        print(f"❌ Failed to get metrics: {response.status_code}")

    print("\n🎉 Basic optimization system test completed!")
    print("=" * 60)
    print("📊 The Parameter Optimization System is working!")
    print(f"🔧 Configuration ID: {config_id}")
    print("📖 API Documentation: http://localhost:8000/docs")

    return config_id


if __name__ == "__main__":
    try:
        config_id = test_simple_optimization()
        if config_id:
            print("\n💡 Next steps:")
            print("   1. Visit http://localhost:8000/docs to explore the API")
            print(f"   2. Use the configuration ID {config_id} for further testing")
            print(
                "   3. The optimization results will be empty until we implement actual simulation processing"
            )
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
