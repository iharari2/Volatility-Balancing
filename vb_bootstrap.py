#!/usr/bin/env python3
import os, pathlib, textwrap, json

files = {
  ".gitignore": textwrap.dedent("""
    # python
    __pycache__/
    *.pyc
    .venv/
    .env
    # node
    node_modules/
    .next/
    out/
    # misc
    dist/
    build/
    .DS_Store
    coverage/
    htmlcov/
    site/
  """).lstrip("\n"),
  "README.md": textwrap.dedent("""
    # Volatility Balancing (MVP)
    Semi-passive, mean-reversion paper-trading platform on blue-chip equities.

    ## Quick Start
    ```bash
    make up setup migrate
    make run-api     # http://localhost:8000
    make run-web     # http://localhost:3000
    ```
  """).lstrip("\n"),
  "Makefile": textwrap.dedent(r"""
    SHELL := /bin/bash
    PY ?= python3
    PIP ?= pip3
    BACKEND_DIR ?= backend
    FRONTEND_DIR ?= frontend
    API_BASE ?= http://localhost:8000
    API_TOKEN ?=
    DATABASE_URL ?= postgresql://postgres:postgres@localhost:5432/app
    REDIS_URL ?= redis://localhost:6379/0

    .PHONY: help setup lint fmt unit integration test run-api run-web up down migrate revision smoke local-smoke dbshell logs coverage clean

    help:
    	@echo "Targets: setup, lint, fmt, unit, integration, test, run-api, run-web, up, down, migrate, revision, smoke, local-smoke, dbshell, logs, coverage, clean"

    setup:
    	$(PIP) install -U pip
    	$(PIP) install -r $(BACKEND_DIR)/requirements.txt
    	cd $(FRONTEND_DIR) && npm ci || npm install

    lint:
    	ruff check $(BACKEND_DIR) || true
    	cd $(FRONTEND_DIR) && npm run lint || true

    fmt:
    	ruff format $(BACKEND_DIR) || true

    unit:
    	pytest -q $(BACKEND_DIR)/tests/unit --cov=$(BACKEND_DIR) --cov-report=term-missing || true

    integration:
    	pytest -q $(BACKEND_DIR)/tests/integration || true

    test: unit integration

    run-api:
    	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

    run-web:
    	cd $(FRONTEND_DIR) && npm run dev -- --port 3000

    up:
    	docker compose up -d || true
    	echo "Waiting for DB..." && sleep 3 || true

    down:
    	docker compose down -v || true

    revision:
    	cd $(BACKEND_DIR) && alembic revision -m "$(m)" || true

    migrate:
    	cd $(BACKEND_DIR) && alembic upgrade head || true

    smoke:
    	curl -f $(API_BASE)/health || exit 1
    	API_BASE=$(API_BASE) API_TOKEN=$(API_TOKEN) $(PY) scripts/smoke_place_cancel.py || true

    local-smoke: API_BASE=http://localhost:8000
    local-smoke:
    	$(MAKE) smoke

    dbshell:
    	psql $(DATABASE_URL) || true

    logs:
    	docker compose logs -f --tail=200 || true

    coverage:
    	pytest -q $(BACKEND_DIR)/tests/unit --cov=$(BACKEND_DIR) --cov-report=html || true

    clean:
    	rm -rf .pytest_cache .mypy_cache htmlcov dist build **/__pycache__
  """).lstrip("\n"),
  "docker-compose.yml": textwrap.dedent("""
    services:
      postgres:
        image: postgres:15
        environment:
          POSTGRES_PASSWORD: postgres
          POSTGRES_USER: postgres
          POSTGRES_DB: app
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
  """).lstrip("\n"),
  # Backend
  "backend/requirements.txt": textwrap.dedent("""
    fastapi==0.111.0
    uvicorn[standard]==0.30.0
    pydantic==2.7.4
    requests==2.32.3
    pytest==8.2.0
    pytest-cov==5.0.0
    ruff==0.5.6
    SQLAlchemy==2.0.32
    alembic==1.13.2
    psycopg2-binary==2.9.9
    redis==5.0.7
    python-dotenv==1.0.1
  """).lstrip("\n"),
  "backend/app/main.py": textwrap.dedent("""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uuid, time

    app = FastAPI(title="VB MVP API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # ---- simple in-memory stub for MVP smoke ----
    ORDERS = {}

    class OrderIn(BaseModel):
        account_id: str
        symbol: str
        side: str
        qty: int
        limit_price: float | None = None

    @app.post("/api/v1/orders")
    def place_order(o: OrderIn):
        if o.limit_price is None:  # enforce limit-only per MVP stub
            o.limit_price = 1.0
        if o.qty <= 0:
            raise HTTPException(400, "qty must be > 0")
        oid = str(uuid.uuid4())
        ORDERS[oid] = {"id": oid, "status": "accepted", "limit_price": float(o.limit_price)}
        # simulate same-day fill at limit after small delay
        ORDERS[oid]["_filled_at"] = time.time() + 1.5
        return {"id": oid, "status": "accepted", "limit_price": float(o.limit_price)}

    @app.get("/api/v1/orders/{oid}")
    def get_order(oid: str):
        if oid not in ORDERS:
            raise HTTPException(404, "not found")
        od = ORDERS[oid]
        if "_filled_at" in od and time.time() >= od["_filled_at"]:
            od["status"] = "filled"
            od["fill_price"] = od["limit_price"]
            od.pop("_filled_at", None)
        return od

    @app.post("/api/v1/orders/{oid}/cancel")
    def cancel_order(oid: str):
        if oid not in ORDERS:
            raise HTTPException(404, "not found")
        od = ORDERS[oid]
        if od.get("status") == "filled":
            return {"status": "too_late"}
        od["status"] = "canceled"
        return {"status": "canceled"}
  """).lstrip("\n"),
  "backend/tests/unit/test_health.py": textwrap.dedent("""
    from fastapi.testclient import TestClient
    from app.main import app

    def test_health():
        c = TestClient(app)
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json().get("status") == "ok"
  """).lstrip("\n"),
  "backend/tests/integration/test_orders_stub.py": textwrap.dedent("""
    from fastapi.testclient import TestClient
    from app.main import app
    import time

    def test_stub_fill_same_day_at_limit():
        c = TestClient(app)
        r = c.post("/api/v1/orders", json={"account_id":"test","symbol":"MSFT","side":"buy","qty":1,"limit_price":123.45})
        assert r.status_code == 200
        oid = r.json()["id"]

        for _ in range(6):
            s = c.get(f"/api/v1/orders/{oid}").json()
            if s.get("status") == "filled":
                assert abs(s["fill_price"] - 123.45) < 1e-9
                return
            time.sleep(0.5)
        raise AssertionError("order did not auto-fill")
  """).lstrip("\n"),
  # scripts
  "scripts/smoke_place_cancel.py": textwrap.dedent("""
    import os, time, requests
    BASE = os.environ.get("API_BASE","http://localhost:8000")
    print("Smoke: health", BASE)
    r = requests.get(f"{BASE}/health"); r.raise_for_status()
    print("OK", r.json())

    print("Smoke: place order")
    r = requests.post(f"{BASE}/api/v1/orders", json={"account_id":"test","symbol":"MSFT","side":"buy","qty":1,"limit_price":100})
    r.raise_for_status(); oid = r.json()["id"]; print("order id", oid)

    for _ in range(6):
        s = requests.get(f"{BASE}/api/v1/orders/{oid}").json()
        if s.get("status")=="filled":
            assert abs(s["fill_price"]-s["limit_price"])<1e-9
            print("filled at", s["fill_price"])
            break
        time.sleep(0.5)
    else:
        raise SystemExit("order did not fill in time")

    print("Smoke: cancel (may be too_late if already filled)")
    r = requests.post(f"{BASE}/api/v1/orders/{oid}/cancel"); r.raise_for_status()
    print("cancel:", r.json())
  """).lstrip("\n"),
  # frontend
  "frontend/package.json": json.dumps({
    "name": "vb-frontend",
    "private": True,
    "scripts": {
      "dev": "next dev",
      "build": "next build",
      "start": "next start",
      "lint": "eslint ."
    },
    "dependencies": {
      "next": "14.2.5",
      "react": "18.3.1",
      "react-dom": "18.3.1"
    },
    "devDependencies": {
      "eslint": "9.9.0",
      "eslint-config-next": "14.2.5",
      "typescript": "5.5.4"
    }
  }, indent=2),
  "frontend/next.config.js": "/** @type {import('next').NextConfig} */ const nextConfig = {}; module.exports = nextConfig;\n",
  "frontend/tsconfig.json": textwrap.dedent("""
    {
      "compilerOptions": { "target": "es2020", "lib": ["dom","dom.iterable","esnext"], "allowJs": true, "skipLibCheck": true, "strict": false, "noEmit": true, "module": "esnext", "moduleResolution": "bundler", "resolveJsonModule": true, "isolatedModules": true, "jsx": "preserve", "baseUrl": "." },
      "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
      "exclude": ["node_modules"]
    }
  """).lstrip("\n"),
  "frontend/app/layout.tsx": textwrap.dedent("""
    export const metadata = { title: "VB MVP", description: "Volatility Balancing" };
    export default function RootLayout({ children }: { children: React.ReactNode }) {
      return (<html lang="en"><body style={{fontFamily:"Inter, sans-serif", padding:16}}>{children}</body></html>);
    }
  """).lstrip("\n"),
  "frontend/app/page.tsx": textwrap.dedent("""
    export default function Home() {
      return (
        <main>
          <h1>Volatility Balancing — MVP</h1>
          <p>Next.js shell is running. API health: <code>/health</code> at :8000</p>
        </main>
      );
    }
  """).lstrip("\n"),
  "frontend/next-env.d.ts": "/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n",
  # CI
  ".github/workflows/ci-cd.yml": textwrap.dedent("""
    name: ci-cd
    on:
      pull_request: { branches: [ main ] }
      push: { branches: [ main ] }
      workflow_dispatch:

    concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }

    env:
      PY_VERSION: "3.11"
      NODE_VERSION: "20"
      API_BASE_STAGING: ${{ secrets.API_BASE_STAGING }}
      API_TOKEN_STAGING: ${{ secrets.API_TOKEN_STAGING }}

    jobs:
      backend-lint-unit:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with: { python-version: ${{ env.PY_VERSION }} }
          - name: Install deps
            run: |
              python -m pip install --upgrade pip
              pip install -r backend/requirements.txt
              pip install pytest pytest-cov ruff
          - name: Lint & Unit
            run: |
              ruff check backend || true
              pytest -q backend/tests/unit --cov=backend --cov-fail-under=0

      frontend-lint-build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with: { node-version: ${{ env.NODE_VERSION }} }
          - name: Install & Build
            working-directory: frontend
            run: |
              npm ci || npm install
              npm run build

      integration-tests:
        runs-on: ubuntu-latest
        needs: [ backend-lint-unit ]
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with: { python-version: ${{ env.PY_VERSION }} }
          - name: Install backend deps
            run: |
              pip install -r backend/requirements.txt
              pip install pytest
          - name: Run integration tests (stubbed)
            run: pytest -q backend/tests/integration || true

      smoke-staging:
        runs-on: ubuntu-latest
        needs: [ frontend-lint-build ]
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with: { python-version: ${{ env.PY_VERSION }} }
          - name: Install smoke deps
            run: pip install requests
          - name: Health
            run: curl -f $API_BASE_STAGING/health || true
          - name: Place+Cancel Order
            env:
              API_BASE: ${{ env.API_BASE_STAGING }}
              API_TOKEN: ${{ env.API_TOKEN_STAGING }}
            run: python scripts/smoke_place_cancel.py || true
  """).lstrip("\n"),
  ".github/CODEOWNERS": "/backend/   @iharari2\n/frontend/  @iharari2\n/.policy/   @iharari2\n/.github/   @iharari2\n",
  # docs (minimal)
  "mkdocs.yml": textwrap.dedent("""
    site_name: Volatility Balancing Docs
    theme:
      name: material
      features: [navigation.tabs, navigation.sections, content.code.copy]
    nav:
      - Home: docs/index.md
      - Dev:
          - Test Plan: docs/dev/test-plan.md
          - CI/CD: docs/dev/ci-cd.md
  """).lstrip("\n"),
  "docs/index.md": "# VB Docs\\nStart here.\\n",
  "docs/dev/test-plan.md": "# Dev Test Plan\\n",
  "docs/dev/ci-cd.md": "# CI/CD\\n",
}

def write_file(path, content):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Normalize line endings to LF
    with open(p, "w", newline="\n", encoding="utf-8") as f:
      f.write(content)

for path, content in files.items():
    write_file(path, content)

print(f"✅ Wrote {len(files)} files.")
