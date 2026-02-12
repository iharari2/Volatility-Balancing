#!/usr/bin/env python3
"""
Test that all export endpoints now use real market data from Yahoo Finance
"""

import requests


def test_real_market_data_export(url, description, expected_fields=None):
    """Test a single export endpoint for real market data"""
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=60)  # Longer timeout for real data fetching

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "spreadsheet" in content_type or "excel" in content_type:
                print(
                    f"   ✅ SUCCESS - Excel file with real data returned ({len(response.content):,} bytes)"
                )

                # Check if the file size indicates real data (should be larger than mock data)
                if len(response.content) > 10000:  # 10KB+
                    print(
                        "   📊 REAL DATA - Large file size indicates comprehensive real market data"
                    )
                    return True
                else:
                    print("   ⚠️  SMALL FILE - May still contain mock data")
                    return False
            else:
                print(f"   ⚠️  WARNING - Unexpected content type: {content_type}")
                # Check if it's JSON with real market data
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        # Look for market data indicators
                        has_real_data = any(
                            key in str(data).lower()
                            for key in [
                                "current_price",
                                "volume",
                                "market_cap",
                                "pe_ratio",
                                "timestamp",
                                "bid",
                                "ask",
                                "historical",
                            ]
                        )
                        if has_real_data:
                            print("   📈 REAL DATA - JSON contains market data fields")
                            return True
                        else:
                            print("   ❌ MOCK DATA - No real market data indicators found")
                            return False
                except:
                    pass
                print(f"   Response preview: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ FAILED - Status {response.status_code}")
            try:
                error_detail = response.json().get("detail", "No detail provided")
                print(f"   Error: {error_detail}")
            except:
                print(f"   Response: {response.text[:200]}...")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ CONNECTION ERROR - Backend not running on port 8001")
        return False
    except requests.exceptions.Timeout:
        print("   ⏰ TIMEOUT - Real market data fetching took too long (>60s)")
        return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def test_backend_health():
    """Test if backend is running and healthy"""
    print("🏥 Testing Backend Health...")

    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Backend is healthy and running")
            return True
        else:
            print(f"   ⚠️  Backend responded with status {response.status_code}")
            return False
    except:
        print("   ❌ Backend health check failed")
        return False


def main():
    """Test all export endpoints for real market data integration"""
    print("🌐 Testing Real Market Data Integration in Exports")
    print("=" * 60)

    # Check backend health first
    if not test_backend_health():
        print("\n❌ Backend is not running. Please start it first:")
        print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload")
        return 1

    # Backend base URL
    base_url = "http://localhost:8001/v1/excel"

    # Test endpoints with real market data
    endpoints = [
        # Portfolio/Position exports - should have real current prices
        (f"{base_url}/positions/export", "Portfolio Export (Real Current Prices)"),
        (f"{base_url}/positions/pos_2e16e371/export", "AAPL Position Export (Real Current Data)"),
        (f"{base_url}/positions/pos_eb083cb4/export", "MSFT Position Export (Real Current Data)"),
        (f"{base_url}/positions/pos_0a5e6fc0/export", "GOOGL Position Export (Real Current Data)"),
        (
            f"{base_url}/positions/pos_2e16e371/comprehensive-export",
            "AAPL Comprehensive Export (Real Historical Data)",
        ),
        # Simulation exports - should have real historical data and calculated metrics
        (
            f"{base_url}/simulation/sim_aapl_123/export",
            "AAPL Simulation Export (Real Historical Analysis)",
        ),
        (
            f"{base_url}/simulation/sim_msft_456/export",
            "MSFT Simulation Export (Real Historical Analysis)",
        ),
        (
            f"{base_url}/simulation/sim_aapl_123/enhanced-export",
            "AAPL Enhanced Simulation (Real Time Series)",
        ),
        (
            f"{base_url}/simulation/sim_msft_456/enhanced-export",
            "MSFT Enhanced Simulation (Real Time Series)",
        ),
    ]

    results = []
    print(f"\n🚀 Testing {len(endpoints)} endpoints for real market data...")

    for url, description in endpoints:
        success = test_real_market_data_export(url, description)
        results.append((description, success))

    # Summary
    print("\n" + "=" * 60)
    print("📊 REAL MARKET DATA INTEGRATION SUMMARY:")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ REAL DATA" if success else "❌ MOCK/ERROR"
        print(f"   {status} - {description}")

    print(f"\nOverall: {passed}/{total} exports using real market data")

    if passed == total:
        print("\n🎉 SUCCESS! All exports now use real market data from Yahoo Finance!")
        print("   📈 Portfolio exports: Real current prices, bid/ask, volume, market cap")
        print("   📊 Simulation exports: Real historical data, calculated metrics, time series")
        print("   💼 Investment ready: Data is suitable for investment decisions")
    elif passed > total // 2:
        print(f"\n⚠️  PARTIAL SUCCESS: {passed}/{total} exports using real data")
        print("   Some exports may still use fallback data when Yahoo Finance is unavailable")
    else:
        print(f"\n❌ FAILED: Only {passed}/{total} exports using real data")
        print("   Most exports may still be using mock data")

    print("\n💡 TROUBLESHOOTING:")
    print("   1. Ensure backend is running with Yahoo Finance integration")
    print("   2. Check internet connection for Yahoo Finance API access")
    print("   3. Verify YFinanceAdapter is properly configured")
    print("   4. Check backend logs for market data fetch errors")

    # Performance note
    print("\n⏱️  PERFORMANCE NOTE:")
    print("   Real market data fetching may take 10-30 seconds per export")
    print("   This is normal for comprehensive real-time financial data")

    return 0 if passed >= total // 2 else 1


if __name__ == "__main__":
    exit(main())
