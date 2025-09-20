import requests
import time
from datetime import datetime, timedelta

# Test performance optimization
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=30)  # 30 days

print('Testing trigger analysis performance optimization:')

# Test 1: Detailed trigger analysis (default)
print('\n--- Test 1: Detailed trigger analysis (default) ---')
start_time = time.time()

try:
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'AAPL',
        'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
        'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
        'initial_cash': 10000,
        'detailed_trigger_analysis': True,
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
    
    detailed_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        triggers = result.get('trigger_analysis', [])
        
        # Check if detailed data is present
        first_trigger = triggers[0] if triggers else {}
        has_detailed_data = 'bid' in first_trigger and 'ask' in first_trigger
        
        print(f'  Execution time: {detailed_time:.2f} seconds')
        print(f'  Total evaluations: {len(triggers)}')
        print(f'  Has detailed data: {has_detailed_data}')
        print(f'  Sample fields: {list(first_trigger.keys())[:10]}')
    else:
        print(f'  Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'  Error: {e}')

# Test 2: Optimized trigger analysis
print('\n--- Test 2: Optimized trigger analysis ---')
start_time = time.time()

try:
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'AAPL',
        'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
        'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
        'initial_cash': 10000,
        'detailed_trigger_analysis': False,  # Optimized mode
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
    
    optimized_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        triggers = result.get('trigger_analysis', [])
        
        # Check if detailed data is present
        first_trigger = triggers[0] if triggers else {}
        has_detailed_data = 'bid' in first_trigger and 'ask' in first_trigger
        
        print(f'  Execution time: {optimized_time:.2f} seconds')
        print(f'  Total evaluations: {len(triggers)}')
        print(f'  Has detailed data: {has_detailed_data}')
        print(f'  Sample fields: {list(first_trigger.keys())[:10]}')
        
        # Performance comparison
        if 'detailed_time' in locals():
            speedup = detailed_time / optimized_time
            print(f'  Performance improvement: {speedup:.2f}x faster')
    else:
        print(f'  Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'  Error: {e}')
