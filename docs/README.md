# Volatility Balancing Documentation

Welcome to the Volatility Balancing trading system documentation. This documentation provides comprehensive guides for understanding, developing, and operating the system.

## 📚 Documentation Structure

### 🚀 [Quick Start Guide](QUICK_START.md)

Get up and running quickly with setup instructions and basic usage.

### 🏗️ [Architecture Documentation](architecture/README.md)

Comprehensive architectural documentation including:

- System context and container views
- Domain model and entities
- Component architecture
- Clean architecture implementation
- Trading cycles and state machines
- Persistence and data models
- **Position Cell Model** - Position as self-contained trading cell (cash + stock)
- **Position Performance KPIs** - Performance measurement (position vs stock)

### 📡 [API Documentation](api/README.md)

Complete API reference and usage guides:

- OpenAPI specification
- Portfolio-scoped endpoints
- Migration guide from deprecated endpoints
- Authentication and error handling

### 💻 [Development Guide](DEVELOPER_NOTES.md)

Developer resources:

- Setup and configuration
- Code organization and patterns
- Testing strategies
- Development workflows

### 📋 [Product Documentation](product/README.md)

Product specifications and requirements:

- Volatility trading specification
- GUI design guidelines
- Feature requirements
- Screen structure (Portfolio, Position, Trade screens)

### 🔧 [Operations](runbooks/README.md)

Operational runbooks and procedures:

- Deployment guides
- Monitoring and troubleshooting
- Backup and recovery

### 👥 [Team Coordination](team-coordination/README.md)

Processes and templates for coordinating Development, QA, UX, and Documentation teams:

- Team lead guide and workflows
- Quality gates and checkpoints
- Test plan and documentation templates
- Release procedures and checklists

### 📝 [Architecture Decision Records](adr/README.md)

Key architectural decisions and their rationale.

## 🎯 Key Concepts

### Portfolio-Scoped Architecture

All data is scoped to tenants and portfolios:

- **Tenants**: Multi-tenant isolation
- **Portfolios**: Independent trading portfolios per tenant
- **Positions**: Scoped to portfolios (each position is a cell with cash + stock)
- **Cash**: Stored in `Position.cash` (position-scoped, not portfolio-level)
- **Orders & Trades**: Portfolio-scoped

**Important**: Legacy `/v1/positions` endpoints have been removed. Use portfolio-scoped endpoints:

- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}` - Create portfolio
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview` - Get overview
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions` - List positions

See [API Migration Guide](api/MIGRATION.md) for details.

### Clean Architecture

The system follows Clean Architecture principles:

- **Domain Layer**: Pure business logic, no dependencies
- **Application Layer**: Use cases and orchestration
- **Infrastructure Layer**: External adapters and implementations
- **Presentation Layer**: API routes and UI components

### Core Features

- **Position Cell Model**: Each position is a self-contained trading cell (cash + stock)
- **Volatility-Triggered Trading**: Automated buy/sell based on price thresholds
- **Portfolio Management**: Multi-portfolio support with position-scoped cash
- **Performance Measurement**: Position performance vs stock performance (alpha calculation)
- **Independent Strategies**: Each position has its own strategy configuration
- **Order Execution**: Idempotent order submission with guardrails
- **Dividend Processing**: Automatic dividend handling and anchor adjustments
- **Audit Trails**: Complete event logging for compliance
- **Real-time Simulation**: Backtesting with production logic

## 🔍 Finding Information

### By Role

**Architect/Designer:**

- Start with [Architecture Overview](architecture/README.md)
- Review [Clean Architecture](architecture/clean_architecture_overview.md)
- Check [Architecture Decision Records](adr/)

**Developer:**

- Read [Developer Notes](DEVELOPER_NOTES.md)
- Review [API Documentation](api/README.md)
- Check [Component Architecture](architecture/component_architecture.md)

**Product Manager:**

- Review [Product Specification](product/volatility_trading_spec_v1.md)
- Check [GUI Design](product/GUI%20design.md)

**DevOps/Operations:**

- Review [Deployment Guide](architecture/deployment.md)
- Check [Runbooks](runbooks/)

**Team Leads/Managers:**

- Review [Team Coordination Guide](team-coordination/README.md)
- Check [Team Lead Guide](team-coordination/TEAM_LEAD_GUIDE.md)
- Use [Quick Reference Checklist](team-coordination/QUICK_REFERENCE_CHECKLIST.md)

### By Topic

**Understanding the System:**

1. [System Context](architecture/context.md) - High-level system boundaries
2. [Domain Model](architecture/domain-model.md) - Core business entities
3. [Trading Cycle](architecture/trading-cycle.md) - How trading works
4. [State Machines](architecture/state-machines.md) - State transitions

**Working with the Code:**

1. [Developer Notes](DEVELOPER_NOTES.md) - Setup and guidelines
2. [Component Architecture](architecture/component_architecture.md) - Code organization
3. [API Documentation](api/README.md) - API reference
4. [Testing Guide](dev/test-plan.md) - Testing strategies

**Deploying and Operating:**

1. [Deployment Guide](architecture/deployment.md) - Deployment procedures
2. [Runbooks](runbooks/) - Operational procedures
3. [Monitoring](architecture/audit.md) - Audit and logging

## 📖 Documentation Standards

### File Naming

- Use lowercase with hyphens: `domain-model.md`
- Be descriptive: `trading-cycle.md` not `trading.md`
- Group related files in folders

### Structure

- Start with a clear title and overview
- Use consistent heading hierarchy
- Include navigation links
- Add "Last updated" dates

### Content

- Keep documentation current with code
- Remove outdated information
- Link to related documents
- Include code examples where helpful

## 🔄 Recent Changes

### 2025-01-XX: Portfolio-Scoped Architecture Migration

- Removed deprecated `/v1/positions` endpoints
- All operations now require `tenant_id` and `portfolio_id`
- See [API Migration Guide](api/MIGRATION.md) for migration details

### Documentation Cleanup

- Reorganized architecture documentation
- Removed duplicate and outdated files
- Added comprehensive navigation

## 🤝 Contributing to Documentation

When updating documentation:

1. Keep it current with code changes
2. Update related documents
3. Add navigation links
4. Remove outdated information
5. Follow the documentation standards above

## 📞 Getting Help

- **Architecture Questions**: See [Architecture Documentation](architecture/README.md)
- **API Questions**: See [API Documentation](api/README.md)
- **Development Questions**: See [Developer Notes](DEVELOPER_NOTES.md)
- **Product Questions**: See [Product Documentation](product/README.md)

---

_Last updated: 2025-01-XX_
