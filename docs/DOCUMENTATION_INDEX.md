# Volatility Balancing - Master Documentation Index

**Last Updated:** 2025-01-27  
**Purpose:** Central navigation hub for all project documentation

---

## 🎯 Quick Navigation by Role

### 👨‍💻 **New Developer? Start Here**

1. [Onboarding Guide](ONBOARDING.md) - Complete setup and first steps
2. [Quick Start Guide](QUICK_START.md) - Get running in 5 minutes
3. [Developer Notes](../docs/DEVELOPER_NOTES.md) - Development guidelines
4. [Architecture Overview](architecture/README.md) - Understand the system

### 🏗️ **Architect/Designer**

1. [Architecture Overview](architecture/README.md) - System architecture
2. [System Context](architecture/context.md) - High-level boundaries
3. [Domain Model](architecture/domain-model.md) - Core business entities
4. [Clean Architecture](architecture/clean_architecture_overview.md) - Architectural principles
5. [Architecture Decision Records](adr/README.md) - Key decisions

### 📊 **Product Manager**

1. [Product Specification](product/volatility_trading_spec_v1.md) - Complete PRD
2. [UX Design Document](UX_DESIGN_DOCUMENT.md) - User experience design
3. [UX Feedback Request](UX_FEEDBACK_REQUEST.md) - Current UX status
4. [GUI Design](product/GUI%20design.md) - Interface specifications

### 🔧 **DevOps/Operations**

1. [Deployment Guide](architecture/deployment.md) - Deployment procedures
2. [Runbooks](runbooks/README.md) - Operational procedures
3. [CI/CD Guide](dev/ci-cd.md) - Continuous integration

### 👥 **Team Lead/Manager**

1. [Team Coordination Guide](team-coordination/README.md) - Team workflows
2. [Team Lead Guide](team-coordination/TEAM_LEAD_GUIDE.md) - Leadership resources
3. [Quick Reference Checklist](team-coordination/QUICK_REFERENCE_CHECKLIST.md) - Daily checklist

---

## 📚 Documentation Structure

### 🚀 Getting Started

- **[Onboarding Guide](ONBOARDING.md)** ⭐ **NEW DEVELOPERS START HERE**

  - Complete setup instructions
  - First code changes
  - Development workflow
  - Common issues and solutions

- **[Quick Start Guide](QUICK_START.md)**

  - Fast setup (5 minutes)
  - Basic usage
  - Troubleshooting

- **[WSL Setup Guide](../WSL_SETUP_GUIDE.md)**
  - Windows Subsystem for Linux setup
  - WSL-specific troubleshooting

### 🏗️ Architecture Documentation

**Location:** `docs/architecture/`

- **[Architecture README](architecture/README.md)** - Main architecture hub
- **[System Context](architecture/context.md)** - System boundaries and users
- **[Containers](architecture/containers.md)** - Major applications/services
- **[Component Architecture](architecture/component_architecture.md)** - Component relationships
- **[Domain Model](architecture/domain-model.md)** - Core business entities
- **[Clean Architecture Overview](architecture/clean_architecture_overview.md)** - Architectural principles
- **[Trading Cycle](architecture/trading-cycle.md)** - Live trading flow
- **[Simulation](architecture/simulation.md)** - Backtesting flow
- **[State Machines](architecture/state-machines.md)** - State transitions
- **[Persistence](architecture/persistence.md)** - Database schema
- **[Deployment](architecture/deployment.md)** - Infrastructure and deployment
- **[Audit & Logging](architecture/audit.md)** - Event logging
- **[Commissions & Dividends](architecture/commissions_dividends_architecture.md)** - Fee handling

**Archive:** Historical/superseded docs in `architecture/archive/`

### 📡 API Documentation

**Location:** `docs/api/`

- **[API README](api/README.md)** - API overview and usage
- **[OpenAPI Specification](api/openapi.yaml)** - Complete API spec
- **[Migration Guide](api/MIGRATION.md)** - API migration procedures
- **[Parameter Optimization API](api/PARAMETER_OPTIMIZATION_API.md)** - Optimization endpoints

### 💻 Development Documentation

**Location:** `docs/dev/`

- **[Developer Notes](../docs/DEVELOPER_NOTES.md)** - Development guidelines
- **[Test Plan](dev/test-plan.md)** - Testing strategy
- **[CI/CD Guide](dev/ci-cd.md)** - Continuous integration
- **[Current Status Summary](dev/current_status_summary.md)** - Project status
- **[Development Plan Status](dev/development_plan_status.md)** - Implementation progress
- **[Unified Development Plan](dev/unified_development_plan.md)** - Roadmap

### 📋 Product Documentation

**Location:** `docs/product/`

- **[Product README](product/README.md)** - Product documentation hub
- **[Volatility Trading Spec](product/volatility_trading_spec_v1.md)** - Complete PRD (✅ Implemented)
- **[GUI Design](product/GUI%20design.md)** - Interface specifications
- **[Parameter Optimization PRD](product/parameter_optimization_prd.md)** - Optimization feature spec (✅ Implemented)

**Unimplemented Features:** `docs/product/unimplemented/`

- **[Unimplemented Features README](product/unimplemented/README.md)** - Overview of planned features
- **[Real-time Data Integration](product/unimplemented/real_time_data_integration.md)** - Yahoo Finance integration
- **[Enhanced Trade Event Logging](product/unimplemented/enhanced_trade_event_logging.md)** - Verbose trader event log
- **[Heat Map Visualization](product/unimplemented/heat_map_visualization.md)** - Parameter optimization visualization
- **[Transaction Details Tracking](product/unimplemented/transaction_details_tracking.md)** - Detailed transaction tracking
- **[Position Change Logging](product/unimplemented/position_change_logging.md)** - Automatic change logging
- **[Debug Export Filtering](product/unimplemented/debug_export_filtering.md)** - Export filtering options

### 🎨 UX Documentation

**Location:** `docs/` (root level)

- **[UX Design Document](UX_DESIGN_DOCUMENT.md)** - Complete UX design
- **[UX Feedback Request](UX_FEEDBACK_REQUEST.md)** - Current UX status
- **[UX Audit](UX_AUDIT.md)** - Technical audit
- **[UX Audit Summary](UX_AUDIT_SUMMARY.md)** - Executive summary
- **[UX Quick Fixes](UX_QUICK_FIXES.md)** - Actionable fixes
- **[UX User Persona Review](UX_USER_PERSONA_REVIEW.md)** - Persona analysis
- **[UX User Type Review](UX_USER_TYPE_REVIEW.md)** - User type analysis
- **[UX Implementation Plan](UX_IMPLEMENTATION_PLAN.md)** - Implementation roadmap

### 🔧 Operations & Runbooks

**Location:** `docs/runbooks/`

- **[Runbooks README](runbooks/README.md)** - Operational procedures
- **[Runbook Template](runbooks/RUNBOOK_TEMPLATE.md)** - Template for new runbooks

### 👥 Team Coordination

**Location:** `docs/team-coordination/`

- **[Team Coordination README](team-coordination/README.md)** - Team workflows
- **[Team Lead Guide](team-coordination/TEAM_LEAD_GUIDE.md)** - Leadership resources
- **[Quick Reference Checklist](team-coordination/QUICK_REFERENCE_CHECKLIST.md)** - Daily checklist
- **[Setup Summary](team-coordination/SETUP_SUMMARY.md)** - Environment setup
- **[Documentation Plan Template](team-coordination/DOCUMENTATION_PLAN_TEMPLATE.md)** - Doc planning
- **[QA Test Plan Template](team-coordination/QA_TEST_PLAN_TEMPLATE.md)** - Test planning
- **[Release Notes Template](team-coordination/RELEASE_NOTES_TEMPLATE.md)** - Release docs

### 📝 Architecture Decision Records

**Location:** `docs/adr/`

- **[ADR README](adr/README.md)** - ADR overview
- **[ADR Template](adr/ADR_TEMPLATE.md)** - Template for new ADRs
- **[Repository Structure ADR](adr/2025-08-26-repo-structure.md)** - Project structure decisions

### 📦 Archive Documentation

**Location:** `docs/archive/`

- **[Archive README](archive/README.md)** - Historical documentation
- **completion-reports/** - Old completion summaries
- **qa-reports/** - Historical QA reports
- **migration-reports/** - Old migration documentation
- **status-reports/** - Historical status reports

⚠️ **Note:** Archive documents are historical and may be outdated. Refer to current documentation in `docs/` for up-to-date information.

---

## 🗺️ Documentation by Topic

### Understanding the System

1. **[System Context](architecture/context.md)** - What the system does and who uses it
2. **[Domain Model](architecture/domain-model.md)** - Core business concepts
3. **[Trading Cycle](architecture/trading-cycle.md)** - How trading works end-to-end
4. **[Product Specification](product/volatility_trading_spec_v1.md)** - What the system should do

### Working with the Code

1. **[Onboarding Guide](ONBOARDING.md)** - Setup and first steps
2. **[Developer Notes](../docs/DEVELOPER_NOTES.md)** - Development guidelines
3. **[Component Architecture](architecture/component_architecture.md)** - Code organization
4. **[API Documentation](api/README.md)** - API reference
5. **[Test Plan](dev/test-plan.md)** - Testing strategies

### Deploying and Operating

1. **[Deployment Guide](architecture/deployment.md)** - Deployment procedures
2. **[Runbooks](runbooks/README.md)** - Operational procedures
3. **[Audit & Logging](architecture/audit.md)** - Monitoring and logging

### Feature-Specific Documentation

- **Parameter Optimization**: [Parameter Optimization API](api/PARAMETER_OPTIMIZATION_API.md), [PRD](product/parameter_optimization_prd.md) (✅ Implemented)
- **Excel Export**: See backend docs (`backend/EXCEL_EXPORT_GUIDE.md`) (✅ Implemented)
- **Portfolio Management**: [API Migration Guide](api/MIGRATION.md) (✅ Implemented)
- **Trading**: [Trading Cycle](architecture/trading-cycle.md), [Product Spec](product/volatility_trading_spec_v1.md) (✅ Implemented)

### Planned Features (Not Yet Implemented)

See [Unimplemented Features](product/unimplemented/README.md) for:
- Real-time data integration (Yahoo Finance)
- Enhanced trade event logging
- Heat map visualization (backend ready)
- Transaction details tracking
- Position change logging
- Debug export filtering

---

## 📊 Documentation Status

### ✅ Up-to-Date Documentation

- Architecture overview and structure
- API documentation (OpenAPI spec)
- Developer notes (order sizing, fill pipeline)
- Product specification
- Clean architecture documentation

### ⚠️ Needs Review/Update

- Some archived architecture documents (in `archive/`)
- Some development status documents (may be outdated)
- UX documentation (awaiting feedback per UX_FEEDBACK_REQUEST.md)

### 📝 Maintenance

See [Documentation Maintenance Guide](DOCUMENTATION_MAINTENANCE.md) for:

- How to keep documentation current
- When to update documentation
- Documentation standards
- Review process

---

## 🔍 Finding What You Need

### By Question Type

**"How do I...?"**

- Setup: [Onboarding Guide](ONBOARDING.md) or [Quick Start](QUICK_START.md)
- Develop: [Developer Notes](../docs/DEVELOPER_NOTES.md)
- Deploy: [Deployment Guide](architecture/deployment.md)
- Test: [Test Plan](dev/test-plan.md)

**"What is...?"**

- System: [System Context](architecture/context.md)
- Architecture: [Architecture README](architecture/README.md)
- Feature: [Product Specification](product/volatility_trading_spec_v1.md)
- Component: [Component Architecture](architecture/component_architecture.md)

**"Why...?"**

- Design decisions: [Architecture Decision Records](adr/README.md)
- Implementation choices: [Clean Architecture Overview](architecture/clean_architecture_overview.md)

**"Where is...?"**

- Code: [Component Architecture](architecture/component_architecture.md)
- API: [API Documentation](api/README.md)
- Database: [Persistence](architecture/persistence.md)

---

## 📞 Getting Help

- **Architecture Questions**: See [Architecture Documentation](architecture/README.md)
- **API Questions**: See [API Documentation](api/README.md)
- **Development Questions**: See [Developer Notes](../docs/DEVELOPER_NOTES.md)
- **Product Questions**: See [Product Documentation](product/README.md)
- **Setup Issues**: See [Onboarding Guide](ONBOARDING.md) or [Quick Start](QUICK_START.md)

---

## 🔄 Recent Documentation Updates

### 2025-01-27

- Created master documentation index
- Added documentation maintenance guide
- Created onboarding guide for new developers
- Updated main README with clearer implementation status
- **Repository cleanup**: Created archive structure and unimplemented features documentation
- **New**: `docs/product/unimplemented/` - Clear documentation of planned features
- **New**: `docs/archive/` - Organized historical documentation

### Previous Updates

- Portfolio-scoped architecture migration documented
- Parameter optimization system documented
- UX design documents created
- Architecture documentation reorganized

---

## 📝 Contributing to Documentation

When updating documentation:

1. **Keep it current** - Update docs when code changes
2. **Link related docs** - Add navigation links
3. **Follow standards** - See [Documentation Maintenance Guide](DOCUMENTATION_MAINTENANCE.md)
4. **Update this index** - Add new docs to appropriate sections
5. **Remove outdated info** - Archive or delete obsolete docs

---

_This index is maintained by the documentation team. Last reviewed: 2025-01-27_







