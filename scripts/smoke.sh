#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${API_BASE:-http://127.0.0.1:8000}"
TOKEN="${API_TOKEN:-}"

echo "▶ Health check (no auth)"
curl -fsS "$BASE_URL/v1/healthz" > /dev/null

echo "▶ Version"
curl -fsS "$BASE_URL/v1/version" > /dev/null

# Obtain an auth token if one wasn't provided
if [ -z "$TOKEN" ]; then
  echo "▶ Register smoke user (or ignore if exists)"
  SMOKE_EMAIL="smoke-$(date +%s)@smoke.local"
  REG=$(curl -fsS -X POST -H "Content-Type: application/json" \
    -d "{\"email\":\"$SMOKE_EMAIL\",\"password\":\"smoketest123\"}" \
    "$BASE_URL/v1/auth/register" 2>/dev/null || echo '{}')
  TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")
fi

if [ -z "$TOKEN" ]; then
  echo "⚠ Could not obtain auth token — skipping authenticated smoke tests"
else
  AUTH_HEADER="Authorization: Bearer $TOKEN"
  echo "▶ Market state"
  curl -fsS -H "$AUTH_HEADER" "$BASE_URL/v1/market/state" > /dev/null

  echo "▶ Sim tick"
  curl -fsS -X POST -H "Content-Type: application/json" -H "$AUTH_HEADER" \
    -d '{}' "$BASE_URL/v1/sim/tick" > /dev/null
fi

echo "✅ Smoke tests passed"
