import requests
from datetime import datetime, timedelta

# Test with 10 days to see bid/ask display
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=10)

print('Testing bid/ask display issue:')

try:
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'AAPL',
        'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
        'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
        'initial_cash': 10000,
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
        
        print(f'Total triggers: {len(triggers)}')
        if triggers:
            first_trigger = triggers[0]
            print('\nFirst trigger bid/ask values:')
            print(f'  Price: {first_trigger.get("price", "N/A")}')
            print(f'  Bid: {first_trigger.get("bid", "N/A")}')
            print(f'  Ask: {first_trigger.get("ask", "N/A")}')
            print(f'  Open: {first_trigger.get("open", "N/A")}')
            print(f'  High: {first_trigger.get("high", "N/A")}')
            print(f'  Low: {first_trigger.get("low", "N/A")}')
            print(f'  Close: {first_trigger.get("close", "N/A")}')
    else:
        print(f'Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'Connection error: {e}')
