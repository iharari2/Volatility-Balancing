import requests
from datetime import datetime, timedelta

# Test simulation presets
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=5)

print('Testing simulation presets:')

# Test 1: Get all presets
print('\n--- Test 1: Get all presets ---')
try:
    response = requests.get('http://localhost:8000/v1/simulation/presets')
    
    if response.status_code == 200:
        result = response.json()
        presets = result.get('presets', [])
        
        print(f'✅ Found {len(presets)} presets:')
        for preset in presets:
            print(f'  - {preset["preset_id"]}: {preset["name"]} - {preset["description"]}')
    else:
        print(f'❌ Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 2: Get specific preset
print('\n--- Test 2: Get specific preset ---')
try:
    response = requests.get('http://localhost:8000/v1/simulation/presets/day_trading')
    
    if response.status_code == 200:
        preset = response.json()
        print(f'✅ Day Trading preset:')
        print(f'  Name: {preset["name"]}')
        print(f'  Description: {preset["description"]}')
        print(f'  Trigger threshold: {preset["position_config"]["trigger_threshold_pct"]*100}%')
        print(f'  Interval: {preset["intraday_interval_minutes"]} minutes')
        print(f'  Max orders per day: {preset["position_config"]["guardrails"]["max_orders_per_day"]}')
    else:
        print(f'❌ Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 3: Run simulation with preset
print('\n--- Test 3: Run simulation with preset ---')
try:
    response = requests.post('http://localhost:8000/v1/simulation/run-with-preset', json={
        'ticker': 'AAPL',
        'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
        'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
        'preset_id': 'swing_trading',
        'initial_cash': 10000
    })
    
    if response.status_code == 200:
        result = response.json()
        preset_used = result.get('preset_used', {})
        
        print(f'✅ Simulation with preset completed:')
        print(f'  Preset: {preset_used.get("name", "Unknown")}')
        print(f'  Total trades: {result.get("total_trades", 0)}')
        print(f'  Return: {result.get("total_return_pct", 0):.2f}%')
        print(f'  Total evaluations: {len(result.get("trigger_analysis", []))}')
    else:
        print(f'❌ Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 4: Test different presets
print('\n--- Test 4: Compare different presets ---')
presets_to_test = ['day_trading', 'swing_trading', 'long_term_investing']

for preset_id in presets_to_test:
    try:
        response = requests.post('http://localhost:8000/v1/simulation/run-with-preset', json={
            'ticker': 'AAPL',
            'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
            'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
            'preset_id': preset_id,
            'initial_cash': 10000
        })
        
        if response.status_code == 200:
            result = response.json()
            preset_used = result.get('preset_used', {})
            trades = result.get('total_trades', 0)
            return_pct = result.get('total_return_pct', 0)
            evaluations = len(result.get('trigger_analysis', []))
            
            print(f'  {preset_id}: {trades} trades, {return_pct:.2f}% return, {evaluations} evaluations')
        else:
            print(f'  {preset_id}: Error {response.status_code}')
    except Exception as e:
        print(f'  {preset_id}: Error {e}')
