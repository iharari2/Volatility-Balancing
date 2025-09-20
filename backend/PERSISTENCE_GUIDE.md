# Portfolio Persistence Guide

This guide explains how to enable persistent storage for portfolios, positions, and trades in the Volatility Balancing system.

## Problem Solved

Previously, portfolios created through the GUI were lost on backend restart because the system defaulted to in-memory storage. This guide shows how to enable persistent storage with proper transaction logging.

## Quick Start

### 1. Enable SQL Persistence

```bash
# Set environment variables
export APP_PERSISTENCE=sql
export APP_EVENTS=sql
export APP_AUTO_CREATE=true

# Or use the provided startup script
python start_with_sql.py
```

### 2. Verify Persistence

1. Create a portfolio through the GUI
2. Restart the backend
3. Check that the portfolio persists

## Architecture

### Data Flow

```mermaid
graph TD
    A[GUI Creates Position] --> B[Position API]
    B --> C[SQLPositionsRepo]
    C --> D[SQLite Database]

    E[Trade Execution] --> F[ExecuteOrderUC]
    F --> G[SQLTradesRepo]
    F --> H[SQLPositionsRepo]
    F --> I[SQLEventsRepo]
    G --> D
    H --> D
    I --> D

    style D fill:#90EE90
```

### Database Schema

The system now includes these persistent tables:

- **positions**: Portfolio positions with order policies and guardrails
- **orders**: Order requests and their status
- **trades**: Actual trade executions (NEW)
- **events**: System events and audit trail

## Configuration Options

### Environment Variables

| Variable          | Default                 | Description                        |
| ----------------- | ----------------------- | ---------------------------------- |
| `APP_PERSISTENCE` | `memory`                | Storage backend: `memory` or `sql` |
| `APP_EVENTS`      | `memory`                | Events storage: `memory` or `sql`  |
| `APP_AUTO_CREATE` | `false`                 | Auto-create database tables        |
| `SQL_URL`         | `sqlite:///./vb.sqlite` | Database connection URL            |

### Database Options

#### SQLite (Development)

```bash
export SQL_URL="sqlite:///./vb.sqlite"
```

#### PostgreSQL (Production)

```bash
export SQL_URL="postgresql://user:pass@localhost:5432/volatility_balancing"
```

## Trade Logging

### What Gets Logged

Every trade execution is now logged with:

- **Trade ID**: Unique identifier
- **Order ID**: Reference to the originating order
- **Position ID**: Reference to the position
- **Side**: BUY or SELL
- **Quantity**: Number of shares
- **Price**: Execution price
- **Commission**: Trading fees
- **Executed At**: Timestamp

### API Endpoints

```bash
# List trades for a position
GET /positions/{position_id}/trades

# List trades for an order
GET /orders/{order_id}/trades
```

## Migration from In-Memory

If you have existing data in memory:

1. **Export positions** (if any exist in memory)
2. **Enable SQL persistence**
3. **Recreate positions** through the GUI
4. **Verify persistence** by restarting

## Troubleshooting

### Database Not Created

```bash
# Run migration script
python migrate_add_trades.py

# Or set auto-create
export APP_AUTO_CREATE=true
```

### Data Not Persisting

1. Check environment variables:

   ```bash
   echo $APP_PERSISTENCE  # Should be "sql"
   echo $SQL_URL          # Should point to valid database
   ```

2. Check database file exists:

   ```bash
   ls -la vb.sqlite
   ```

3. Check logs for errors

### Performance Considerations

- **SQLite**: Good for development and small deployments
- **PostgreSQL**: Recommended for production with high volume
- **Indexes**: Automatically created for efficient queries

## Version Compatibility

The new trade logging system is backward compatible:

- Existing positions will work with new system
- Old events are preserved
- New trades are logged alongside existing data

## Security Notes

- Database files should be backed up regularly
- Use proper file permissions for database files
- Consider encryption for sensitive production data
- Use connection pooling for high-volume deployments
