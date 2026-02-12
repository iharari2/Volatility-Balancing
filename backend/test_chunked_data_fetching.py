import requests
from datetime import datetime, timedelta

# Test chunked data fetching for longer periods
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=30)  # 30 days - should trigger chunked fetching

print('Testing chunked data fetching (30 days):')

try:
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'AAPL',
        'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
        'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
        'initial_cash': 10000,
        'intraday_interval_minutes': 30,
        'position_config': {
            'trigger_threshold_pct': 0.01,
            'rebalance_ratio': 0.5,
            'commission_rate': 0.001,
            'min_notional': 100,
            'allow_after_hours': True,
            'guardrails': {
                'min_stock_alloc_pct': 0.25,
                'max_stock_alloc_pct': 0.75,
                'max_orders_per_day': 10
            }
        },
        'include_after_hours': True
    })
    
    if response.status_code == 200:
        result = response.json()
        triggers = result.get('trigger_analysis', [])
        
        print('✅ Chunked data fetching completed')
        print(f'  Total evaluations: {len(triggers)}')
        
        # Check if we have minute-by-minute data (more data points than daily)
        expected_daily = 30 * 14  # 30 days × 14 evaluations per day
        actual = len(triggers)
        ratio = actual / expected_daily if expected_daily > 0 else 0
        
        print(f'  Expected evaluations (daily): {expected_daily}')
        print(f'  Actual evaluations: {actual}')
        print(f'  Ratio: {ratio:.2f}')
        
        if ratio > 1.5:  # Significantly more than daily
            print('  ✅ High resolution data detected (likely minute-by-minute)')
        elif ratio > 0.8:
            print('  ✅ Good data coverage')
        else:
            print('  ❌ Low data coverage - may not be using chunked fetching')
        
        # Check for data quality
        if triggers:
            first_trigger = triggers[0]
            print(f'  Sample fields: {list(first_trigger.keys())[:10]}')
            
            # Check if we have detailed OHLC data
            has_ohlc = all(field in first_trigger for field in ['open', 'high', 'low', 'close'])
            print(f'  Has OHLC data: {has_ohlc}')
    else:
        print(f'❌ Simulation failed: {response.status_code} - {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')
