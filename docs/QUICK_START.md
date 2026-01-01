# Quick Start Guide

Get up and running with Volatility Balancing in minutes.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL** (for production) or **SQLite** (for development)
- **Git**

## 🚀 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd Volatility-Balancing
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run database migrations (if needed)
# (SQLite will be created automatically on first run)

# Start backend server
python -m uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 🎯 First Steps

### 1. Create a Portfolio

```bash
curl -X POST "http://localhost:8000/api/tenants/default/portfolios" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Portfolio",
    "type": "SIM",
    "starting_cash": {"currency": "USD", "amount": 100000},
    "holdings": [
      {"asset": "AAPL", "qty": 10, "anchor_price": 150.0}
    ],
    "template": "DEFAULT",
    "hours_policy": "OPEN_ONLY"
  }'
```

Save the `portfolio_id` from the response.

### 2. View Portfolio Overview

```bash
curl "http://localhost:8000/api/tenants/default/portfolios/{portfolio_id}/overview"
```

### 3. Access Interactive API Docs

Visit `http://localhost:8000/docs` for Swagger UI with interactive API testing.

## 📚 Next Steps

- Read [Architecture Documentation](architecture/README.md) to understand the system
- Review [API Documentation](api/README.md) for API usage
- Check [Developer Notes](DEVELOPER_NOTES.md) for development guidelines

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Change port
python -m uvicorn app.main:app --reload --port 8001
```

**Database errors:**
- SQLite database is created automatically in `backend/volatility_balancing.db`
- For PostgreSQL, ensure database exists and connection string is correct

### Frontend Issues

**Port already in use:**
```bash
# Change port
npm run dev -- --port 3001
```

**Module not found:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## 🔗 Additional Resources

- [WSL Setup Guide](../WSL_SETUP_GUIDE.md) - For WSL users
- [Architecture Documentation](architecture/README.md) - System architecture
- [API Documentation](api/README.md) - API reference

---

_Last updated: 2025-01-XX_









