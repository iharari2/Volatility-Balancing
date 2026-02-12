#!/usr/bin/env python3
import requests

print("🚀 Testing Demo Setup...")
print("=" * 40)

# Test server connectivity
try:
    response = requests.get("http://localhost:8000/v1/healthz")
    print("✅ Server is running")
except Exception:
    print("❌ Server not running")
    exit(1)

# Test position creation
response = requests.post(
    "http://localhost:8000/v1/positions", json={"ticker": "AAPL", "qty": 0, "cash": 10000}
)
if response.status_code == 201:
    pos_id = response.json()["id"]
    print(f"✅ Position created: {pos_id}")

    # Test anchor setting
    response = requests.post(f"http://localhost:8000/v1/positions/{pos_id}/anchor?price=150.0")
    if response.status_code == 200:
        print("✅ Anchor price set")

        # Test evaluation
        response = requests.post(
            f"http://localhost:8000/v1/positions/{pos_id}/evaluate?current_price=145.0"
        )
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Evaluation working: {data["trigger_detected"]} - {data["reasoning"]}')
            print("\n🎉 Demo is ready to go!")
        else:
            print("❌ Evaluation failed")
    else:
        print("❌ Anchor setting failed")
else:
    print("❌ Position creation failed")

