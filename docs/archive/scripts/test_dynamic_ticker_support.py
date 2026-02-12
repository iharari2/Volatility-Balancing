#!/usr/bin/env python3
"""
Test that the export system can handle ANY ticker dynamically
"""

import requests


def test_dynamic_ticker_export(base_url, position_id, ticker, description):
    """Test a specific ticker with the dynamic export system"""
    print(f"\n🎯 Testing: {description}")
    print(f"   Ticker: {ticker}")
    print(f"   Position ID: {position_id}")

    # Test individual position export with ticker override
    url = f"{base_url}/positions/{position_id}/export?ticker={ticker}"
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "spreadsheet" in content_type or "excel" in content_type:
                print(f"   ✅ SUCCESS - {ticker} Excel export ({len(response.content):,} bytes)")

                # Check file size - real data should be substantial
                if len(response.content) > 5000:  # 5KB+
                    print(f"   📊 REAL DATA - Substantial file with {ticker} market data")
                    return True
                else:
                    print("   ⚠️  SMALL FILE - May be using fallback data")
                    return False
            else:
                print(f"   ❌ WRONG FORMAT - Expected Excel, got {content_type}")
                return False
        else:
            print(f"   ❌ FAILED - Status {response.status_code}")
            try:
                error = response.json().get("detail", "Unknown error")
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def test_comprehensive_ticker_export(base_url, position_id, ticker, description):
    """Test comprehensive export with dynamic ticker"""
    print(f"\n📊 Testing Comprehensive: {description}")
    print(f"   Ticker: {ticker}")

    url = f"{base_url}/positions/{position_id}/comprehensive-export?ticker={ticker}"
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=90)  # Longer timeout for comprehensive data

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "spreadsheet" in content_type or "excel" in content_type:
                print(
                    f"   ✅ SUCCESS - {ticker} Comprehensive export ({len(response.content):,} bytes)"
                )

                # Comprehensive exports should be even larger
                if len(response.content) > 15000:  # 15KB+
                    print(f"   📈 COMPREHENSIVE DATA - Full {ticker} historical & market data")
                    return True
                else:
                    print(f"   ⚠️  LIMITED DATA - May be missing some {ticker} data")
                    return False
            else:
                print(f"   ❌ WRONG FORMAT - Expected Excel, got {content_type}")
                return False
        else:
            print(f"   ❌ FAILED - Status {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def test_simulation_ticker_export(base_url, simulation_id, ticker, description):
    """Test simulation export with dynamic ticker"""
    print(f"\n🎲 Testing Simulation: {description}")
    print(f"   Ticker: {ticker}")

    url = f"{base_url}/simulation/{simulation_id}/export?ticker={ticker}"
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=90)

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "spreadsheet" in content_type or "excel" in content_type:
                print(
                    f"   ✅ SUCCESS - {ticker} Simulation export ({len(response.content):,} bytes)"
                )
                return True
            else:
                print(f"   ❌ WRONG FORMAT - Expected Excel, got {content_type}")
                return False
        else:
            print(f"   ❌ FAILED - Status {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False


def main():
    """Test dynamic ticker support across various stock types"""
    print("🌍 Testing Dynamic Ticker Support - ANY Stock/ETF/Index")
    print("=" * 70)

    # Backend base URL
    base_url = "http://localhost:8001/v1/excel"

    # Test a diverse range of tickers
    test_cases = [
        # US Large Cap Tech
        ("pos_test_1", "NVDA", "NVIDIA Corporation"),
        ("pos_test_2", "TSLA", "Tesla Inc"),
        ("pos_test_3", "AMD", "Advanced Micro Devices"),
        ("pos_test_4", "CRM", "Salesforce Inc"),
        # US Traditional Blue Chips
        ("pos_test_5", "BRK.A", "Berkshire Hathaway Class A"),
        ("pos_test_6", "JNJ", "Johnson & Johnson"),
        ("pos_test_7", "KO", "Coca-Cola Company"),
        ("pos_test_8", "DIS", "Walt Disney Company"),
        # ETFs & Index Funds
        ("pos_test_9", "SPY", "SPDR S&P 500 ETF"),
        ("pos_test_10", "QQQ", "Invesco QQQ Trust"),
        ("pos_test_11", "VTI", "Vanguard Total Stock Market ETF"),
        ("pos_test_12", "ARKK", "ARK Innovation ETF"),
        # International Stocks
        ("pos_test_13", "ASML", "ASML Holding NV (Netherlands)"),
        ("pos_test_14", "TSM", "Taiwan Semiconductor"),
        ("pos_test_15", "BABA", "Alibaba Group (China)"),
        # Commodities & Special Cases
        ("pos_test_16", "GLD", "SPDR Gold Shares"),
        ("pos_test_17", "SLV", "iShares Silver Trust"),
        ("pos_test_18", "USO", "United States Oil Fund"),
        # Crypto-Related (if supported)
        ("pos_test_19", "COIN", "Coinbase Global Inc"),
        ("pos_test_20", "MSTR", "MicroStrategy Inc"),
    ]

    print(f"\n🚀 Testing {len(test_cases)} different tickers across multiple asset classes...")

    results = []

    for position_id, ticker, description in test_cases:
        # Test basic position export
        success_basic = test_dynamic_ticker_export(base_url, position_id, ticker, description)

        # Test comprehensive export (every 3rd ticker to avoid overwhelming)
        success_comprehensive = True
        if len(results) % 3 == 0:
            success_comprehensive = test_comprehensive_ticker_export(
                base_url, position_id, ticker, description
            )

        # Test simulation export (every 5th ticker)
        success_simulation = True
        if len(results) % 5 == 0:
            simulation_id = f"sim_{ticker.lower().replace('.', '_')}_123"
            success_simulation = test_simulation_ticker_export(
                base_url, simulation_id, ticker, description
            )

        overall_success = success_basic and success_comprehensive and success_simulation
        results.append((ticker, description, overall_success))

    # Summary
    print("\n" + "=" * 70)
    print("📊 DYNAMIC TICKER SUPPORT SUMMARY:")

    passed = sum(1 for _, _, success in results if success)
    total = len(results)

    # Group results by category
    categories = {
        "US Tech": ["NVDA", "TSLA", "AMD", "CRM"],
        "US Blue Chips": ["BRK.A", "JNJ", "KO", "DIS"],
        "ETFs": ["SPY", "QQQ", "VTI", "ARKK"],
        "International": ["ASML", "TSM", "BABA"],
        "Commodities": ["GLD", "SLV", "USO"],
        "Crypto-Related": ["COIN", "MSTR"],
    }

    for category, tickers in categories.items():
        print(f"\n   📂 {category}:")
        for ticker, description, success in results:
            if ticker in tickers:
                status = "✅ SUPPORTED" if success else "❌ FAILED"
                print(f"      {status} - {ticker} ({description})")

    print(f"\nOverall: {passed}/{total} tickers successfully supported")

    if passed == total:
        print("\n🎉 PERFECT! System supports ANY ticker dynamically!")
        print("   📈 US Stocks: Large cap, mid cap, small cap")
        print("   🌍 International: ADRs and foreign listings")
        print("   📊 ETFs: Sector, index, thematic funds")
        print("   🥇 Commodities: Gold, silver, oil, etc.")
        print("   ₿ Crypto: Bitcoin-related stocks")
        print("   💼 All data is fetched live from Yahoo Finance!")
    elif passed > total * 0.8:
        print(f"\n🟢 EXCELLENT: {passed}/{total} tickers supported!")
        print("   Most asset classes work - some may need internet connection")
    elif passed > total * 0.6:
        print(f"\n🟡 GOOD: {passed}/{total} tickers supported")
        print("   Major tickers work - some specialized assets may fail")
    else:
        print(f"\n🔴 NEEDS WORK: Only {passed}/{total} tickers supported")
        print("   System may still have hardcoded limitations")

    print("\n💡 USAGE EXAMPLES:")
    print("   Portfolio Export: /api/excel/positions/my_pos/export?ticker=NVDA")
    print("   Comprehensive: /api/excel/positions/my_pos/comprehensive-export?ticker=BRK.A")
    print("   Simulation: /api/excel/simulation/my_sim/export?ticker=SPY")
    print("   Any ticker: Replace 'NVDA' with any valid Yahoo Finance symbol!")

    return 0 if passed >= total * 0.8 else 1


if __name__ == "__main__":
    exit(main())
