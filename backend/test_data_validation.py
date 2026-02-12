import requests
from datetime import datetime, timedelta

# Test data validation
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=5)

print('Testing data validation:')

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
        
        print('✅ Simulation completed successfully')
        print(f'  Total evaluations: {len(triggers)}')
        
        # Check if we have any data quality issues in the response
        if 'data_quality' in result:
            quality = result['data_quality']
            print(f'  Data quality score: {quality.get("quality_score", "N/A")}/100')
            print(f'  Issues: {quality.get("errors", 0)} errors, {quality.get("warnings", 0)} warnings')
        else:
            print('  No data quality information in response')
        
        # Check sample trigger data for quality
        if triggers:
            first_trigger = triggers[0]
            print(f'  Sample trigger fields: {list(first_trigger.keys())}')
            
            # Check for required fields
            required_fields = ['timestamp', 'price', 'anchor_price', 'price_change_pct']
            missing_fields = [field for field in required_fields if field not in first_trigger]
            if missing_fields:
                print(f'  ❌ Missing required fields: {missing_fields}')
            else:
                print('  ✅ All required fields present')
    else:
        print(f'❌ Simulation failed: {response.status_code} - {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')
