#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ec2-user/apps/Volatility-Balancing"
VENV_DIR="$APP_ROOT/venv"

REF="${1:-origin/main}"

echo "▶ Deploying ref: $REF"

cd "$APP_ROOT"

echo "▶ Fetching"
git fetch origin

echo "▶ Checking out $REF"
git checkout "$REF"

echo "▶ Ensuring venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "▶ Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "▶ Restarting service"
sudo systemctl restart volbalancing

echo "▶ Running smoke tests"
./scripts/smoke.sh

echo "✅ Deploy completed successfully"

