# API Migration Guide

This guide helps you migrate from deprecated legacy endpoints to the new portfolio-scoped API endpoints.

## 🎯 Overview

The Volatility Balancing API has been migrated to a **portfolio-scoped architecture**. All legacy `/v1/positions` endpoints have been removed and replaced with portfolio-scoped endpoints that require `tenant_id` and `portfolio_id`.

## ⚠️ Breaking Changes

### Removed Endpoints

All legacy endpoints now return **HTTP 410 (Gone)** with a message directing you to the replacement endpoint:

- ❌ `POST /v1/positions`
- ❌ `GET /v1/positions`
- ❌ `GET /v1/positions/{position_id}`
- ❌ `DELETE /v1/positions/{position_id}`
- ❌ `POST /v1/positions/{position_id}/orders`
- ❌ `GET /v1/positions/{position_id}/orders`
- ❌ `POST /v1/positions/{position_id}/evaluate`
- ❌ `POST /v1/positions/{position_id}/evaluate/market`
- ❌ `POST /v1/positions/{position_id}/anchor`
- ❌ `PUT /v1/positions/{position_id}/anchor-price`
- ❌ `GET /v1/positions/{position_id}/events`
- ❌ `POST /v1/positions/{position_id}/orders/auto-size`
- ❌ `POST /v1/positions/update-anchor-prices`
- ❌ `POST /v1/positions/auto-setup`
- ❌ `POST /v1/positions/clear-positions`

### New Architecture

All operations are now **portfolio-scoped**:
- Every request requires `tenant_id` and `portfolio_id`
- Positions belong to portfolios
- Cash is managed at the portfolio level
- Orders and trades are portfolio-scoped

## 🔄 Migration Steps

### Step 1: Create a Portfolio

**Before (deprecated):**
```bash
# This no longer works
POST /v1/positions
{
  "ticker": "AAPL",
  "qty": 10,
  "cash": 10000
}
```

**After (portfolio-scoped):**
```bash
POST /api/tenants/{tenant_id}/portfolios
{
  "name": "My Portfolio",
  "description": "Portfolio description",
  "type": "LIVE",  # or "SIM" or "SANDBOX"
  "starting_cash": {
    "currency": "USD",
    "amount": 10000
  },
  "holdings": [
    {
      "asset": "AAPL",
      "qty": 10,
      "anchor_price": 150.0,  # Optional
      "avg_cost": 150.0        # Optional
    }
  ],
  "template": "DEFAULT",
  "hours_policy": "OPEN_ONLY"  # or "OPEN_PLUS_AFTER_HOURS"
}
```

**Response:**
```json
{
  "portfolio_id": "PBAL-001"
}
```

### Step 2: Get Portfolio Overview

**Before (deprecated):**
```bash
# This no longer works
GET /v1/positions
GET /v1/positions/{position_id}
```

**After (portfolio-scoped):**
```bash
# Get complete portfolio overview
GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview

# Get all positions in portfolio
GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions

# Get specific position
GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}
```

**Overview Response:**
```json
{
  "portfolio": {
    "id": "PBAL-001",
    "name": "My Portfolio",
    "state": "READY",
    "type": "LIVE"
  },
  "cash": {
    "currency": "USD",
    "cash_balance": 10000.0,
    "reserved_cash": 0.0
  },
  "positions": [
    {
      "asset": "AAPL",
      "qty": 10,
      "anchor": 150.0,
      "avg_cost": 150.0
    }
  ],
  "config_effective": {
    "trigger_up_pct": 3.0,
    "trigger_down_pct": -3.0,
    "min_stock_pct": 20,
    "max_stock_pct": 80
  },
  "kpis": {
    "total_value": 115000.0,
    "stock_pct": 13.0,
    "pnl_pct": 0.0
  }
}
```

### Step 3: Submit Orders

**Before (deprecated):**
```bash
# This no longer works
POST /v1/positions/{position_id}/orders
{
  "side": "BUY",
  "qty": 5
}
```

**After (portfolio-scoped):**
```bash
POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders
{
  "side": "BUY",
  "qty": 5
}
```

**With Idempotency:**
```bash
POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders
Headers:
  Idempotency-Key: unique-request-id-123
Body:
{
  "side": "BUY",
  "qty": 5
}
```

### Step 4: List Orders

**Before (deprecated):**
```bash
# This no longer works
GET /v1/positions/{position_id}/orders
```

**After (portfolio-scoped):**
```bash
GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders?limit=100
```

## 📝 Code Migration Examples

### Python Example

**Before:**
```python
import requests

# Create position (deprecated)
response = requests.post(
    "http://localhost:8000/v1/positions",
    json={"ticker": "AAPL", "qty": 10, "cash": 10000}
)

# Get positions (deprecated)
response = requests.get("http://localhost:8000/v1/positions")
```

**After:**
```python
import requests

tenant_id = "default"
portfolio_id = "my-portfolio"

# Create portfolio with positions
response = requests.post(
    f"http://localhost:8000/api/tenants/{tenant_id}/portfolios",
    json={
        "name": "My Portfolio",
        "starting_cash": {"currency": "USD", "amount": 10000},
        "holdings": [{"asset": "AAPL", "qty": 10}]
    }
)
portfolio_id = response.json()["portfolio_id"]

# Get portfolio overview
response = requests.get(
    f"http://localhost:8000/api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview"
)
overview = response.json()
```

### JavaScript/TypeScript Example

**Before:**
```typescript
// Deprecated - no longer works
const createPosition = async (ticker: string, qty: number) => {
  const response = await fetch('/v1/positions', {
    method: 'POST',
    body: JSON.stringify({ ticker, qty, cash: 10000 })
  });
  return response.json();
};
```

**After:**
```typescript
// Portfolio-scoped
const createPortfolio = async (
  tenantId: string,
  name: string,
  holdings: Holding[]
) => {
  const response = await fetch(
    `/api/tenants/${tenantId}/portfolios`,
    {
      method: 'POST',
      body: JSON.stringify({
        name,
        starting_cash: { currency: 'USD', amount: 10000 },
        holdings
      })
    }
  );
  const { portfolio_id } = await response.json();
  return portfolio_id;
};

const getPortfolioOverview = async (
  tenantId: string,
  portfolioId: string
) => {
  const response = await fetch(
    `/api/tenants/${tenantId}/portfolios/${portfolioId}/overview`
  );
  return response.json();
};
```

## 🧪 Testing Migration

### Update Integration Tests

All integration tests using legacy endpoints need to be updated:

**Before:**
```python
def test_create_position():
    response = client.post("/v1/positions", json={
        "ticker": "AAPL",
        "qty": 10,
        "cash": 10000
    })
    assert response.status_code == 201
```

**After:**
```python
def test_create_portfolio():
    # Create portfolio
    response = client.post(
        "/api/tenants/default/portfolios",
        json={
            "name": "Test Portfolio",
            "starting_cash": {"currency": "USD", "amount": 10000},
            "holdings": [{"asset": "AAPL", "qty": 10}]
        }
    )
    assert response.status_code == 201
    portfolio_id = response.json()["portfolio_id"]
    
    # Get overview
    response = client.get(
        f"/api/tenants/default/portfolios/{portfolio_id}/overview"
    )
    assert response.status_code == 200
    assert len(response.json()["positions"]) == 1
```

## 🔍 Common Issues

### Issue: Getting 410 Gone Errors

**Problem:** Legacy endpoints return 410 Gone.

**Solution:** Update all API calls to use portfolio-scoped endpoints. See examples above.

### Issue: Missing tenant_id/portfolio_id

**Problem:** New endpoints require `tenant_id` and `portfolio_id`.

**Solution:** 
1. Use a default tenant_id (e.g., "default") for single-tenant scenarios
2. Create a portfolio first to get a `portfolio_id`
3. Store `portfolio_id` for subsequent requests

### Issue: Position IDs Changed

**Problem:** Position IDs may have changed in the new architecture.

**Solution:** Position IDs are now scoped to portfolios. Use:
```
GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}
```

## 📚 Additional Resources

- [API Documentation](README.md) - Complete API reference
- [Architecture Documentation](../architecture/README.md) - System architecture
- [Deprecated Endpoints Summary](../../DEPRECATED_REMOVAL_SUMMARY.md) - List of removed endpoints

## ✅ Migration Checklist

- [ ] Identify all code using legacy `/v1/positions` endpoints
- [ ] Create portfolios for existing positions
- [ ] Update API calls to use portfolio-scoped endpoints
- [ ] Update integration tests
- [ ] Update frontend API client
- [ ] Test all migrated endpoints
- [ ] Remove legacy endpoint references from code
- [ ] Update documentation

---

_Last updated: 2025-01-XX_









