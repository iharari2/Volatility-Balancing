# API Documentation

Complete API reference and usage guides for the Volatility Balancing trading system.

## 📡 API Overview

The Volatility Balancing API is a RESTful API built with FastAPI. All operations are **portfolio-scoped**, meaning they require `tenant_id` and `portfolio_id` parameters.

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: (configured per environment)

### API Versioning
- Current version: Portfolio-scoped endpoints (no version prefix)
- Legacy `/v1/*` endpoints have been **removed** (return 410 Gone)

## 🚀 Quick Start

### Authentication
(Add authentication details when implemented)

### Making Requests
All portfolio-scoped endpoints follow this pattern:
```
/api/tenants/{tenant_id}/portfolios/{portfolio_id}/...
```

Example:
```bash
curl -X GET "http://localhost:8000/api/tenants/default/portfolios/my-portfolio/overview"
```

## 📚 API Reference

### OpenAPI Specification
- **[OpenAPI Spec](openapi.yaml)** - Complete API specification in OpenAPI 3.0 format
- **Interactive Docs**: Visit `http://localhost:8000/docs` when the server is running

### Core Endpoints

#### Portfolio Management
- `POST /api/tenants/{tenant_id}/portfolios` - Create portfolio
- `GET /api/tenants/{tenant_id}/portfolios` - List portfolios
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}` - Get portfolio
- `PUT /api/tenants/{tenant_id}/portfolios/{portfolio_id}` - Update portfolio
- `DELETE /api/tenants/{tenant_id}/portfolios/{portfolio_id}` - Delete portfolio
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview` - Get portfolio overview

#### Positions
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions` - List positions
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}` - Get position

#### Orders
- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders` - Submit order
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders` - List orders
- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders/auto-size` - Auto-size order

#### Market Data
- `GET /v1/market/price/{ticker}` - Get current price
- `GET /v1/market/historical/{ticker}` - Get historical data

## 🔄 Migration from Legacy Endpoints

### Deprecated Endpoints (Removed)

The following legacy endpoints have been **removed** and return HTTP 410 (Gone):

- ❌ `POST /v1/positions` → Use `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}`
- ❌ `GET /v1/positions` → Use `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions`
- ❌ `GET /v1/positions/{position_id}` → Use `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}`
- ❌ `POST /v1/positions/{position_id}/orders` → Use `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders`
- ❌ `GET /v1/positions/{position_id}/orders` → Use `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders`

### Migration Guide

See [API Migration Guide](MIGRATION.md) for detailed migration instructions.

### Quick Migration Examples

**Creating a Position (Old → New):**
```bash
# OLD (deprecated - returns 410)
POST /v1/positions
{
  "ticker": "AAPL",
  "qty": 10,
  "cash": 10000
}

# NEW (portfolio-scoped)
POST /api/tenants/default/portfolios/my-portfolio
{
  "name": "My Portfolio",
  "starting_cash": {"currency": "USD", "amount": 10000},
  "holdings": [{"asset": "AAPL", "qty": 10}]
}
```

**Getting Positions (Old → New):**
```bash
# OLD (deprecated - returns 410)
GET /v1/positions

# NEW (portfolio-scoped)
GET /api/tenants/default/portfolios/my-portfolio/positions
```

**Submitting Orders (Old → New):**
```bash
# OLD (deprecated - returns 410)
POST /v1/positions/{position_id}/orders
{
  "side": "BUY",
  "qty": 5
}

# NEW (portfolio-scoped)
POST /api/tenants/default/portfolios/my-portfolio/positions/{position_id}/orders
{
  "side": "BUY",
  "qty": 5
}
```

## 📋 Request/Response Formats

### Common Request Headers
```
Content-Type: application/json
Idempotency-Key: <optional-unique-key>  # For order submission
```

### Common Response Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `404 Not Found` - Resource not found
- `410 Gone` - Endpoint removed (use new endpoint)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

## 🔐 Idempotency

Order submission endpoints support idempotency via the `Idempotency-Key` header:

```bash
curl -X POST "http://localhost:8000/api/tenants/default/portfolios/my-portfolio/positions/pos-123/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-request-id-123" \
  -d '{"side": "BUY", "qty": 10}'
```

Submitting the same request with the same idempotency key will return the original response without creating a duplicate order.

## 📊 Rate Limiting

(Add rate limiting details when implemented)

## 🧪 Testing

### Interactive API Documentation
When the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Example Requests

**Create Portfolio:**
```bash
curl -X POST "http://localhost:8000/api/tenants/default/portfolios" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Portfolio",
    "description": "My test portfolio",
    "type": "SIM",
    "starting_cash": {"currency": "USD", "amount": 100000},
    "holdings": [
      {"asset": "AAPL", "qty": 10, "anchor_price": 150.0}
    ],
    "template": "DEFAULT",
    "hours_policy": "OPEN_ONLY"
  }'
```

**Get Portfolio Overview:**
```bash
curl -X GET "http://localhost:8000/api/tenants/default/portfolios/my-portfolio/overview"
```

**Submit Order:**
```bash
curl -X POST "http://localhost:8000/api/tenants/default/portfolios/my-portfolio/positions/pos-123/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-123" \
  -d '{
    "side": "BUY",
    "qty": 5
  }'
```

## 📖 Additional Resources

- [OpenAPI Specification](openapi.yaml) - Complete API spec
- [API Migration Guide](MIGRATION.md) - Migrating from legacy endpoints
- [Architecture Documentation](../architecture/README.md) - System architecture

## 🔗 Related Documentation

- [Developer Notes](../DEVELOPER_NOTES.md) - Development guidelines
- [Product Specification](../product/volatility_trading_spec_v1.md) - Product requirements

---

_Last updated: 2025-01-XX_









