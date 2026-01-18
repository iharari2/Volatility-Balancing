#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://127.0.0.1:8000"

echo "▶ Health check"
curl -fsS "$BASE_URL/v1/healthz" > /dev/null

echo "▶ Market state"
curl -fsS "$BASE_URL/v1/market/state" > /dev/null

echo "▶ Sim tick"
curl -fsS -X POST -H "Content-Type: application/json" -d '{}' "$BASE_URL/v1/sim/tick" > /dev/null

echo "✅ Smoke tests passed"
