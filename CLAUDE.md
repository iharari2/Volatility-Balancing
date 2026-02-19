# Volatility-Balancing

A deterministic, guardrail-based trading robot for managing a single equity position plus cash, supporting simulation based on historical data, analytics, and live trading.

## Tech Stack

<!-- List the main technologies used in this project -->

 **Frontend**
- React
- Vite
- JavaScript or TypeScript
- Runs locally via Vite dev server (5173 / 5174)

 **Backend**
- Python 3.12
- FastAPI
- Uvicorn
- Domain-driven internal structure

 **Data**
- PostgreSQL
- Redis
- Bound to localhost only

 **Infrastructure**
- GitHub (source of truth)
- Docker Compose (local dev convenience only)
- EC2 (runtime)
- systemd for backend process
- SSM only for access (no inbound ports)


## Project Structure

<!-- Document the folder structure of your project -->

```
Volatility-Balancing/
├── frontend/                    # React + Vite app
│   ├── src/
│   ├── index.html
│   ├── vite.config.*
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── domain/
│   │   └── services/
│   ├── conftest.py
│   └── tests/
│
├── scripts/
│   ├── vb-deploy                # EC2 deploy script
│   └── smoke.sh
│
├── docker-compose.yml           # Local dev only
├── requirements.txt
├── requirements-base.txt
├── CLAUDE.md
└── .claude/
    ├── PRD.md                # Product requirements
    └── reference/            # Best practices docs
```

## Commands

<!-- List the essential commands for running, building, and testing the project -->

```bash
# Install dependencies


# Run development server


# Run tests


# Build for production

# backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# verify
curl http://127.0.0.1:8000/v1/healthz

# Frontend (local)
cd frontend
npm install
npm run dev

# Frontend must use:
VITE_API_BASE_URL=http://127.0.0.1:8000


```

## MCP Servers

<!-- List any MCP servers that should be used with this project -->

**Playwright MCP** is available for browser automation and E2E testing:
```bash
claude mcp add playwright npx @playwright/mcp@latest
```

## Reference Documentation

<!-- Point to reference docs that should be read when working on specific areas -->

| Document | When to Read |
|----------|--------------|
| `.claude/PRD.md` | Understanding requirements, features, API spec |
| `.claude/reference/use-cases.md` | Detailed user flows and interaction diagrams |

## Code Conventions

<!-- Document the coding standards and patterns used in this project -->

### General
- **Never use fake, mock, or randomly generated data in production code.** All features must operate on real data (real market prices, real simulation results, real computations). Stubs and mocks are only acceptable in tests.

### Backend
-

### Frontend
-

### API Design
-

### API Contract Principles
- All APIs are versioned under /v1
- Routes live under backend/app/routes
- Business logic lives under domain or services
- Routes should be thin
- Example: /v1/positions/{position_id}/tick

## Logging

<!-- Describe the logging approach used in this project -->

## Database

<!-- Document the database setup, schema, and any important configuration -->

## Testing Strategy

<!-- Describe how testing is organized in this project -->

### Testing Pyramid
- **Unit tests**:
- **Integration tests**:
- **E2E tests**:

### Test Organization
```
tests/
├── unit/
├── integration/
└── e2e/
```
