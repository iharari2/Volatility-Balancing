import requests
from datetime import datetime, timedelta

print('Testing error handling:')

# Test 1: Invalid ticker
print('\n--- Test 1: Invalid ticker ---')
try:
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'INVALID_TICKER_12345',
        'start_date': '2024-01-01T00:00:00Z',
        'end_date': '2024-01-02T00:00:00Z',
        'initial_cash': 10000
    })
    
    if response.status_code == 200:
        print('❌ Should have failed for invalid ticker')
    else:
        print(f'✅ Correctly failed: {response.status_code} - {response.json().get("detail", "No detail")}')
except Exception as e:
    print(f'✅ Correctly failed: {e}')

# Test 2: Invalid date range
print('\n--- Test 2: Invalid date range ---')
try:
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'AAPL',
        'start_date': '2024-01-02T00:00:00Z',
        'end_date': '2024-01-01T00:00:00Z',  # End before start
        'initial_cash': 10000
    })
    
    if response.status_code == 200:
        print('❌ Should have failed for invalid date range')
    else:
        print(f'✅ Correctly failed: {response.status_code} - {response.json().get("detail", "No detail")}')
except Exception as e:
    print(f'✅ Correctly failed: {e}')

# Test 3: Valid request
print('\n--- Test 3: Valid request ---')
try:
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=5)
    
    response = requests.post('http://localhost:8000/v1/simulation/run', json={
        'ticker': 'AAPL',
        'start_date': start_date.strftime('%Y-%m-%dT00:00:00Z'),
        'end_date': end_date.strftime('%Y-%m-%dT00:00:00Z'),
        'initial_cash': 10000
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f'✅ Valid request succeeded: {len(result.get("trigger_analysis", []))} evaluations')
    else:
        print(f'❌ Valid request failed: {response.status_code} - {response.json().get("detail", "No detail")}')
except Exception as e:
    print(f'❌ Valid request failed: {e}')
