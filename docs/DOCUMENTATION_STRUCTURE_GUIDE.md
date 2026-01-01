# Documentation Structure Guide

**Purpose:** Guide to understanding the repository documentation organization  
**Last Updated:** 2025-01-27

---

## 📁 Overview

The Volatility Balancing repository has been organized into a clear, logical structure to make it easy for new team members to find information and understand the project.

---

## 🎯 Documentation Organization Principles

1. **Current vs Historical** - Current docs in `docs/`, historical in `docs/archive/`
2. **Implemented vs Planned** - Implemented features in main docs, planned in `docs/product/unimplemented/`
3. **Role-Based Navigation** - Documentation organized by audience (developers, architects, PMs, etc.)
4. **Single Source of Truth** - One authoritative document per topic

---

## 📂 Directory Structure

```
docs/
├── README.md                          # Documentation hub
├── ONBOARDING.md                      # ⭐ Start here for new developers
├── QUICK_START.md                     # Fast setup guide
├── DOCUMENTATION_INDEX.md             # Master navigation
├── DOCUMENTATION_STATUS.md            # Documentation health
├── DOCUMENTATION_MAINTENANCE.md       # Maintenance guide
│
├── architecture/                      # System architecture (CURRENT)
│   ├── README.md
│   ├── context.md
│   ├── domain-model.md
│   ├── trading-cycle.md
│   └── archive/                        # Historical architecture docs
│
├── api/                               # API documentation (CURRENT)
│   ├── README.md
│   ├── openapi.yaml
│   └── MIGRATION.md
│
├── product/                           # Product specifications
│   ├── README.md
│   ├── volatility_trading_spec_v1.md  # Main spec (✅ Implemented)
│   └── unimplemented/                 # 📋 Planned features
│       ├── README.md
│       ├── real_time_data_integration.md
│       ├── enhanced_trade_event_logging.md
│       ├── heat_map_visualization.md
│       ├── transaction_details_tracking.md
│       ├── position_change_logging.md
│       └── debug_export_filtering.md
│
├── dev/                               # Development guides (CURRENT)
│   ├── test-plan.md
│   ├── ci-cd.md
│   └── ...
│
├── archive/                           # 📦 Historical documentation
│   ├── README.md
│   ├── completion-reports/            # Old completion summaries
│   ├── qa-reports/                   # Historical QA reports
│   ├── migration-reports/            # Old migration docs
│   └── status-reports/               # Historical status reports
│
├── team-coordination/                 # Team processes (CURRENT)
├── runbooks/                          # Operations (CURRENT)
└── adr/                               # Architecture decisions (CURRENT)
```

---

## 🎯 Key Directories Explained

### `docs/` (Root)

**Current, active documentation** for the project.

- **Getting Started**: `ONBOARDING.md`, `QUICK_START.md`
- **Navigation**: `DOCUMENTATION_INDEX.md`, `DOCUMENTATION_STATUS.md`
- **UX Documentation**: UX design, audits, implementation plans
- **Architecture**: System design and structure
- **API**: API reference and guides
- **Product**: Product specifications

### `docs/product/unimplemented/`

**Planned but not yet implemented features.**

Each feature document includes:
- Status (Planned / In Progress / Blocked)
- Priority (High / Medium / Low)
- Current state
- Requirements
- Dependencies
- Implementation notes
- Acceptance criteria

**Purpose:** Clear documentation of future work, making it easy to:
- Understand what's planned
- Plan implementation
- Track progress
- Onboard new developers

### `docs/archive/`

**Historical documentation** preserved for reference.

Organized by type:
- **completion-reports/**: Old implementation summaries
- **qa-reports/**: Historical QA testing reports
- **migration-reports/**: Old migration documentation
- **status-reports/**: Historical status documents

**⚠️ Important:** Archive documents may be outdated. Always verify against current documentation.

### `docs/architecture/archive/`

**Historical architecture documentation** that has been superseded.

---

## 📋 File Naming Conventions

### Current Documentation

- Use descriptive names: `trading-cycle.md`, `domain-model.md`
- Use lowercase with hyphens: `quick-start.md` not `QuickStart.md`
- Be specific: `parameter-optimization-api.md` not `api.md`

### Archive Documentation

- Keep original names for historical reference
- Organized in subdirectories by type

### Unimplemented Features

- Descriptive feature names: `real-time-data-integration.md`
- Clear and specific: `heat-map-visualization.md`

---

## 🔍 Finding Documentation

### For New Developers

1. **Start Here:**
   - `README.md` (root) - Project overview
   - `docs/ONBOARDING.md` - Complete setup guide
   - `docs/QUICK_START.md` - Fast setup

2. **Then Read:**
   - `docs/DOCUMENTATION_INDEX.md` - Master navigation
   - `docs/architecture/README.md` - System architecture
   - `docs/DEVELOPER_NOTES.md` - Development guidelines

### For Understanding Features

1. **Implemented Features:**
   - `docs/product/volatility_trading_spec_v1.md` - Main product spec
   - `docs/api/` - API documentation
   - `docs/architecture/` - Architecture docs

2. **Planned Features:**
   - `docs/product/unimplemented/README.md` - Overview
   - Individual feature docs in `docs/product/unimplemented/`

### For Historical Context

1. **Archive:**
   - `docs/archive/README.md` - Archive overview
   - Subdirectories by type (completion-reports, qa-reports, etc.)

2. **Architecture History:**
   - `docs/architecture/archive/` - Historical architecture docs

---

## ✅ Status Indicators

Documentation uses clear status indicators:

- **✅ Implemented** - Feature is complete and documented
- **🚧 In Progress** - Feature is being developed
- **📋 Planned** - Feature is planned but not started
- **⏸️ Blocked** - Feature is blocked by dependencies
- **📦 Archived** - Document is historical/reference only

---

## 🔄 Maintenance

### When to Update Documentation

1. **Code Changes** - Update relevant docs when code changes
2. **Feature Completion** - Move from `unimplemented/` to main docs
3. **Obsolete Docs** - Move to `archive/` when superseded
4. **New Features** - Document in `unimplemented/` when planning

### Documentation Lifecycle

```
New Feature Planned
    ↓
Document in docs/product/unimplemented/
    ↓
Implementation Starts
    ↓
Update status to "In Progress"
    ↓
Feature Complete
    ↓
Move to main documentation
    ↓
Remove from unimplemented/
```

---

## 📚 Related Documents

- [Documentation Index](DOCUMENTATION_INDEX.md) - Master navigation
- [Documentation Status](DOCUMENTATION_STATUS.md) - Documentation health
- [Documentation Maintenance](DOCUMENTATION_MAINTENANCE.md) - Maintenance guide
- [Repository Cleanup Plan](REPOSITORY_CLEANUP_PLAN.md) - Cleanup details
- [Archive README](archive/README.md) - Archive information

---

## 🎯 Quick Reference

**New Developer?**
→ Start with `docs/ONBOARDING.md`

**Looking for a feature?**
→ Check `docs/product/` for implemented, `docs/product/unimplemented/` for planned

**Need historical context?**
→ See `docs/archive/` (but verify against current docs)

**Understanding architecture?**
→ See `docs/architecture/README.md`

**API questions?**
→ See `docs/api/README.md`

**What's implemented vs planned?**
→ See `docs/product/unimplemented/README.md` for summary

---

_Last updated: 2025-01-27_



