# Price Comparison Guide

## Issue Found

The GUI was showing **fake calculated prices** instead of real market data!

### Root Cause

In `PortfolioContext.tsx`, the `currentPrice` was being calculated as:
```typescript
const currentPrice = basePrice * (1 + stableVariation * 0.04); // ±2% variation
```

This created a fake price based on anchor price, not real market data.

## Fix Applied

1. **Updated `PortfolioContext.tsx`**: Now uses anchor_price as currentPrice (no fake variation)
2. **Updated `PositionCard.tsx`**: Now fetches real market prices using `useMarketPrice` hook
3. **Backend**: Always fetches fresh data (cache bypassed)

## How to Compare

### Method 1: Check Backend API Directly

```bash
# Get market price from API
curl http://localhost:8000/v1/market/price/AAPL
```

Look for:
- `price`: The current price
- `timestamp`: When data was fetched
- `data_age_seconds`: How old the data is
- `is_fresh`: Whether data is fresh

### Method 2: Check Frontend Browser Console

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter for `/api/market/price/`
4. Click on a request
5. Check Response tab - see what price is returned

### Method 3: Use Comparison Script

```bash
python3 check_price_comparison.py AAPL
```

This will show:
- What the API returns
- What YFinance directly returns
- Data age and freshness

## Expected Behavior Now

✅ **PositionCard**: Shows real market price (fetched via `useMarketPrice`)
✅ **PositionDetail**: Shows real market price (fetched via `useMarketPrice`)
✅ **Market API**: Always returns fresh data (cache bypassed)
✅ **Backend Logs**: Show which data source is used

## What Changed

### Before:
- GUI showed: Fake calculated price (anchor_price ± 2%)
- Market API: Could return stale cached data

### After:
- GUI shows: Real market price from API
- Market API: Always fetches fresh data
- Components: Use `useMarketPrice` hook for real-time prices

## Test It

1. **Restart backend** (to clear cache):
   ```bash
   cd backend
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Check backend logs** - Should see:
   ```
   🔍 Fetching FRESH market data for AAPL (cache bypassed)
   ✅ Using fast_info for AAPL: $XXX.XX (fresh data)
   ```

3. **Check GUI** - Position cards should show:
   - Real current price (from market API)
   - Green dot (●) if fresh, yellow dot (○) if stale

4. **Compare**:
   - GUI price should match API price
   - Both should be current (not weeks old)

## If Still Seeing Issues

1. **Check browser console** for API errors
2. **Check backend logs** for data source used
3. **Clear cache**: `curl -X POST "http://localhost:8000/v1/market/cache/clear"`
4. **Restart frontend** to clear React Query cache

---

**Note**: YFinance free tier has 15-20 minute delay. For real-time data, you'd need a paid provider.



































