# EC2 Deployment Runbook

Complete guide for deploying and running the Volatility-Balancing application on an EC2 instance.

---

## Prerequisites

### EC2 Instance

- **AMI:** Amazon Linux 2023 (AL2023)
- **Instance type:** t3.small or larger
- **Storage:** 20 GB gp3
- **Access:** SSM Session Manager only (no inbound SSH ports)
- **IAM role:** Attach an instance profile with `AmazonSSMManagedInstanceCore` policy

### Software (install on EC2)

```bash
# Python 3.12
sudo dnf install python3.12 python3.12-pip python3.12-devel -y

# Node.js 20 (for frontend build)
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install nodejs -y

# PostgreSQL 15
sudo dnf install postgresql15-server -y
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Redis 7
sudo dnf install redis7 -y
sudo systemctl enable redis7
sudo systemctl start redis7

# Git
sudo dnf install git -y

# Build tools (needed for some Python packages)
sudo dnf groupinstall "Development Tools" -y
```

### PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql <<SQL
CREATE USER vb_user WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE volatility_balancing OWNER vb_user;
GRANT ALL PRIVILEGES ON DATABASE volatility_balancing TO vb_user;
SQL
```

---

## Initial Setup

### 1. Clone the Repository

```bash
sudo mkdir -p /home/ec2-user/apps
sudo chown ec2-user:ec2-user /home/ec2-user/apps
cd /home/ec2-user/apps

git clone https://github.com/YOUR_ORG/Volatility-Balancing.git
cd Volatility-Balancing
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with production values:

```bash
# Required changes from defaults:
APP_PERSISTENCE=sql
APP_EVENTS=sql
SQL_URL=postgresql://vb_user:CHANGE_ME@127.0.0.1:5432/volatility_balancing
APP_BROKER=stub          # Change to "alpaca" when ready for live trading
TRADING_WORKER_ENABLED=true

# If using Alpaca paper trading:
# APP_BROKER=alpaca
# ALPACA_API_KEY=your_key
# ALPACA_SECRET_KEY=your_secret
# ALPACA_PAPER=true

# First deploy only (creates tables automatically):
APP_AUTO_CREATE=true
```

### 3. Backend Setup

```bash
cd /home/ec2-user/apps/Volatility-Balancing

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Backend Starts

```bash
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
sleep 3
curl -f http://127.0.0.1:8000/v1/healthz
# Should return {"status":"ok"} or similar
kill %1
```

After first successful startup with `APP_AUTO_CREATE=true`, set it to `false` in `.env` to prevent accidental table recreation.

### 5. Frontend Build

```bash
cd /home/ec2-user/apps/Volatility-Balancing/frontend

npm ci
VITE_API_BASE_URL=http://YOUR_DOMAIN:8000 npm run build
```

The built static files land in `frontend/dist/`. Serve them via nginx (see below).

### 6. Install systemd Service

```bash
sudo cp docs/runbooks/volbalancing.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable volbalancing
sudo systemctl start volbalancing
```

Verify:

```bash
sudo systemctl status volbalancing
curl -f http://127.0.0.1:8000/v1/healthz
```

### 7. Nginx Setup (Frontend + Reverse Proxy)

```bash
sudo dnf install nginx -y
```

Create `/etc/nginx/conf.d/volbalancing.conf`:

```nginx
server {
    listen 80;
    server_name _;

    # Frontend static files
    root /home/ec2-user/apps/Volatility-Balancing/frontend/dist;
    index index.html;

    # API reverse proxy
    location /v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Routine Deployment

### Automated (CI/CD)

Pushes to `main` trigger the GitHub Actions workflow (`.github/workflows/ci-cd.yml`):

1. Lints backend (ruff) and frontend (eslint + build)
2. Runs unit tests and integration tests
3. Runs `check_trading_safety.py` (warns if market is open)
4. Deploys via SSM `send-command` executing `deploy.sh`
5. Runs post-deploy smoke test
6. Creates a version tag (`vYYYY.MM.DD`)

### Manual (via SSM)

```bash
# Connect to EC2
aws ssm start-session --target i-INSTANCE_ID

# Run deploy script
cd /home/ec2-user/apps/Volatility-Balancing
./deploy.sh                        # Deploy origin/main
./deploy.sh v2025.02.10            # Deploy specific tag
./deploy.sh --tag-version          # Deploy and create version tag
```

The `deploy.sh` script:
1. Runs trading safety check (market hours, active positions, pending orders)
2. Fetches latest code from origin
3. Checks out the specified ref
4. Recreates/updates the Python virtual environment
5. Installs dependencies
6. Restarts the `volbalancing` systemd service
7. Runs smoke tests (`scripts/smoke.sh`)

---

## Start / Stop / Restart

```bash
# Backend service
sudo systemctl start volbalancing
sudo systemctl stop volbalancing
sudo systemctl restart volbalancing

# View logs
sudo journalctl -u volbalancing -f              # Live tail
sudo journalctl -u volbalancing --since "1h ago" # Last hour
sudo journalctl -u volbalancing -n 100           # Last 100 lines

# Nginx
sudo systemctl restart nginx
```

---

## Health Verification

### Quick Check

```bash
curl -f http://127.0.0.1:8000/v1/healthz
```

### Smoke Test

```bash
cd /home/ec2-user/apps/Volatility-Balancing
./scripts/smoke.sh
```

Smoke test verifies:
- `/v1/healthz` responds
- `/v1/market/state` responds
- `/v1/sim/tick` POST succeeds

### Trading Safety Check

```bash
cd /home/ec2-user/apps/Volatility-Balancing
source venv/bin/activate
API_BASE=http://127.0.0.1:8000 python scripts/check_trading_safety.py
```

Checks:
- US market hours (warns if open)
- Active trading positions
- Pending orders
- Trading worker status

---

## Rollback

### Using deploy.sh

```bash
cd /home/ec2-user/apps/Volatility-Balancing
./deploy.sh --rollback
```

This finds the previous version tag and deploys it. To rollback further, run again.

### Manual Rollback

```bash
cd /home/ec2-user/apps/Volatility-Balancing

# List available version tags
git tag -l "v*" --sort=-creatordate | head -10

# Deploy specific version
./deploy.sh v2025.01.27

# Or manually:
git fetch origin --tags
git checkout v2025.01.27
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart volbalancing
./scripts/smoke.sh
```

---

## Rebuilding the Frontend

When frontend code changes, rebuild and restart nginx:

```bash
cd /home/ec2-user/apps/Volatility-Balancing/frontend
npm ci
VITE_API_BASE_URL=http://YOUR_DOMAIN:8000 npm run build
sudo systemctl restart nginx
```

Note: The `deploy.sh` script currently only deploys the backend. Frontend rebuild is a manual step.

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u volbalancing -n 50

# Common issues:
# - Missing .env file → cp .env.example .env
# - PostgreSQL not running → sudo systemctl start postgresql
# - Wrong SQL_URL → verify credentials in .env
# - Port 8000 already in use → lsof -i :8000
```

### Database connection errors

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U vb_user -d volatility_balancing -h 127.0.0.1 -c "SELECT 1;"

# Check pg_hba.conf allows local connections
sudo cat /var/lib/pgsql/data/pg_hba.conf
# Ensure: local all all md5
#    and: host all all 127.0.0.1/32 md5
```

### Trading worker not running

```bash
# Check if worker is enabled in .env
grep TRADING_WORKER_ENABLED .env

# Check worker status via API
curl http://127.0.0.1:8000/v1/trading/worker/status
```

### Service keeps restarting

```bash
# Check for crash loop
sudo systemctl status volbalancing
sudo journalctl -u volbalancing --since "10 min ago"

# Check if dependencies (postgres, redis) are up
sudo systemctl status postgresql redis7
```

---

## Environment Variables Reference

See `.env.example` at the project root for the complete list of environment variables with descriptions and defaults.

Key variables for production:

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_PERSISTENCE` | Yes | `sql` | Storage backend: `sql` or `memory` |
| `SQL_URL` | Yes | - | PostgreSQL connection string |
| `APP_BROKER` | Yes | `stub` | Broker: `stub` or `alpaca` |
| `TRADING_WORKER_ENABLED` | No | `true` | Enable continuous trading loop |
| `ALPACA_API_KEY` | If broker=alpaca | - | Alpaca API key |
| `ALPACA_SECRET_KEY` | If broker=alpaca | - | Alpaca secret key |
| `ALPACA_PAPER` | No | `true` | Use Alpaca paper trading |

---

## Security Notes

- The backend binds to `127.0.0.1` only (not `0.0.0.0`). All external access goes through nginx.
- The systemd service runs with `NoNewPrivileges=true` and `ProtectSystem=strict`.
- EC2 access is via SSM only (no SSH inbound rules).
- Never commit `.env` or credentials to git. The `.env` file is listed in `.gitignore`.
- Alpaca credentials go in `.env` on the EC2 instance only.
