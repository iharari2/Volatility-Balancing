# Operational Runbooks

Operational procedures and runbooks for deploying, monitoring, and maintaining the Volatility Balancing system.

## 📋 Available Runbooks

### Deployment
- **[Deployment Guide](../architecture/deployment.md)** - Infrastructure and deployment procedures

### Monitoring
- **[Audit & Logging](../architecture/audit.md)** - Event logging and audit trails

## 🔧 Common Operations

### Starting the System

**Backend:**
```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Database Operations

**Backup:**
```bash
# SQLite
cp backend/volatility_balancing.db backend/backups/backup-$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U user -d volatility_balancing > backup-$(date +%Y%m%d).sql
```

**Restore:**
```bash
# SQLite
cp backend/backups/backup-YYYYMMDD.db backend/volatility_balancing.db

# PostgreSQL
psql -U user -d volatility_balancing < backup-YYYYMMDD.sql
```

## 📊 Monitoring

### Health Checks

**Backend Health:**
```bash
curl http://localhost:8000/health
```

**API Status:**
```bash
curl http://localhost:8000/api/status
```

### Logs

**Backend Logs:**
- Check console output when running with `--reload`
- Logs directory: `backend/logs/`
- Audit trail: `backend/logs/audit_trail.jsonl`

**Frontend Logs:**
- Check browser console
- Check terminal output

## 🔗 Related Documentation

- [Architecture Documentation](../architecture/README.md) - System architecture
- [Developer Notes](../DEVELOPER_NOTES.md) - Development guidelines

---

_Last updated: 2025-01-XX_









