import requests
from datetime import datetime, timedelta

# Test different intraday intervals
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=10)

print('Testing configurable intraday intervals:')

intervals_to_test = [15, 30, 60]

for interval in intervals_to_test:
    print(f'\n--- Testing {interval}-minute intervals ---')
    
    try:
        response = requests.post('http://localhost:8000/v1/simulation/run', json={
            'ticker': 'AAPL',
            'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
            'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
            'initial_cash': 10000,
            'intraday_interval_minutes': interval,
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
            
            # Count unique times per day
            unique_times = set(trigger.get('time', '') for trigger in triggers)
            unique_times_count = len(unique_times)
            
            print(f'  Total evaluations: {len(triggers)}')
            print(f'  Unique times per day: {unique_times_count}')
            print(f'  Sample times: {sorted(list(unique_times))[:8]}')
            
            # Calculate expected evaluations
            expected_per_day = unique_times_count
            actual_total = len(triggers)
            expected_total = expected_per_day * 10  # 10 days
            print(f'  Expected evaluations: {expected_total} ({expected_per_day} per day × 10 days)')
            print(f'  Actual evaluations: {actual_total}')
            print(f'  Ratio: {actual_total/expected_total:.2f}')
        else:
            print(f'  Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'  Connection error: {e}')
