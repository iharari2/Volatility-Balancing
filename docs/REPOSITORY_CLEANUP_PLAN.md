# Repository Cleanup Plan

**Date:** 2025-01-27  
**Purpose:** Organize documentation and files for easy onboarding and maintenance  
**Status:** In Progress

---

## 📋 Overview

This document outlines the cleanup and organization of the Volatility Balancing repository to create a coherent, easy-to-navigate structure for new team members.

---

## 🎯 Goals

1. **Clear Documentation Structure** - Easy to find current, relevant documentation
2. **Obsolete File Management** - Archive or remove outdated files
3. **Unimplemented Specs** - Clear structure for future features
4. **Onboarding Ready** - New team members can quickly understand the project

---

## 📁 New Documentation Structure

```
docs/
├── README.md                          # Main documentation hub
├── ONBOARDING.md                      # Start here for new developers
├── QUICK_START.md                     # Fast setup guide
│
├── architecture/                      # System architecture (CURRENT)
│   ├── README.md
│   ├── context.md
│   ├── domain-model.md
│   ├── trading-cycle.md
│   ├── persistence.md
│   └── archive/                       # Historical architecture docs
│
├── api/                               # API documentation (CURRENT)
│   ├── README.md
│   ├── openapi.yaml
│   └── MIGRATION.md
│
├── product/                           # Product specifications
│   ├── README.md
│   ├── volatility_trading_spec_v1.md  # Main product spec (IMPLEMENTED)
│   └── unimplemented/                 # Future features
│       ├── README.md
│       ├── heat_map_visualization.md
│       ├── real_time_data_integration.md
│       ├── transaction_details_tracking.md
│       └── position_change_logging.md
│
├── dev/                               # Development guides (CURRENT)
│   ├── test-plan.md
│   ├── ci-cd.md
│   └── archive/                       # Historical dev docs
│
├── team-coordination/                 # Team processes (CURRENT)
│   └── ...
│
├── archive/                           # OBSOLETE documentation
│   ├── completion-reports/            # Old completion summaries
│   ├── status-reports/                # Old status documents
│   ├── migration-reports/             # Old migration docs
│   └── qa-reports/                    # Old QA documents
│
└── runbooks/                          # Operations (CURRENT)
    └── ...
```

---

## 📂 Root Directory Cleanup

### Files to Move to Archive

**Completion/Status Reports (Move to `docs/archive/completion-reports/`):**
- `IMPLEMENTATION_COMPLETE.md`
- `IMPLEMENTATION_SUMMARY.md`
- `TEST_COMPLETION_SUMMARY.md`
- `POSITION_COCKPIT_FINAL_SUMMARY.md`
- `POSITION_COCKPIT_IMPLEMENTATION_SUMMARY.md`
- `EXCEL_EXPORT_FEATURE_COMPLETION.md`
- `EXCEL_EXPORT_INTEGRATION_SUMMARY.md`
- `PORTFOLIO_CASH_REMOVAL_SUMMARY.md`
- `PORTFOLIO_SCOPED_MIGRATION_STATUS.md`
- `QA_MIGRATION_COMPLETE.md`
- `QA_INTEGRATION_TESTS_COMPLETE.md`
- `QA_UNIT_TEST_FIXES_COMPLETE.md`
- `QA_UNIT_TEST_FIXES_FINAL.md`
- `QA_REGRESSION_TEST_FIXES_FINAL.md`
- `QA_REGRESSION_TEST_FIXES.md`
- `FIXES_IMPLEMENTATION_SUMMARY.md`
- `REGRESSION_FIX_SUMMARY.md`
- `TYPE_FIXES_SUMMARY.md`

**QA/Testing Reports (Move to `docs/archive/qa-reports/`):**
- `QA_*.md` files (except `QA_QUICK_START.md` which should be merged into main QUICK_START)
- `TEST_DEVELOPMENT_STATUS.md`
- `TEST_FIXES_NEEDED.md`
- `TEST_GAPS_ANALYSIS.md`
- `TEST_IMPLEMENTATION_PLAN.md`

**Migration/Status Documents (Move to `docs/archive/migration-reports/`):**
- `MIGRATION_INSTRUCTIONS.md` (if superseded by `docs/api/MIGRATION.md`)
- `DATABASE_MIGRATION_INSTRUCTIONS.md`
- `CURRENT_VS_TARGET_MAPPING.md`
- `RECONCILIATION_PROGRESS.md`
- `RECONCILIATION_STATUS.md`
- `CASH_RECONCILIATION_PLAN.md`

**Debugging/Diagnostic Documents (Move to `docs/archive/` or keep if still useful):**
- `DEBUGGING_GUIDE.md` → Move to `docs/runbooks/` if still relevant
- `TIMELINE_DEBUGGING_GUIDE.md` → Archive
- `QUICK_FIX_GUIDE.md` → Archive
- `FINAL_DIAGNOSIS.md` → Archive
- `FIX_DATABASE.md` → Archive
- `FIX_STALE_DATA.md` → Archive
- `PRICE_COMPARISON.md` → Archive
- `TRADE_EXECUTION_ISSUES_REPORT.md` → Move to `docs/archive/` or `docs/runbooks/`

**Planning Documents (Review and archive if obsolete):**
- `CLEANUP_PLAN.md` → This file (keep for reference)
- `DEPRECATED_REMOVAL_PLAN.md` → Archive
- `DEPRECATED_REMOVAL_SUMMARY.md` → Archive
- `NEXT_STEPS.md` → Review, archive if obsolete
- `REMAINING_IMPLEMENTATION.md` → Move to `docs/product/unimplemented/` (update content)
- `ARCHITECTURE_REVIEW.md` → Review, archive if obsolete

**Duplicate/Obsolete Guides:**
- `QUICK_START_GUI.md` → Merge into main `QUICK_START.md`
- `QUICK_START_WSL.md` → Merge into main `QUICK_START.md` or `docs/ONBOARDING.md`
- `WSL_SETUP_GUIDE.md` → Keep in root or move to `docs/`
- `WSL_VERIFY_STEPS.md` → Archive or merge
- `VERIFY_GUI.md` → Archive
- `PHASE1_VERIFY.md` → Archive or move to `docs/dev/`
- `PLAY_GUIDE.md` → Review, archive if obsolete
- `START_DEV_ENVIRONMENT.md` → Merge into `docs/ONBOARDING.md`

**Test Files in Root (Move to `backend/tests/root/` or delete):**
- `test_*.py` files
- `check_*.py` files
- `verify_*.py` files
- `run_*_tests.py` files

**HTML Test Files (Delete or move to `tools/`):**
- `*.html` test files in root

**Obsolete Files:**
- `tatus` (typo file, delete)
- `volatility_balancing_prd_gui_lockup_v_1.md` → Archive or delete
- `README_CLEAN.md` → Delete (if README.md is current)

---

## 📝 Unimplemented Features Documentation

### Create `docs/product/unimplemented/` Directory

**Purpose:** Clear documentation of planned but not yet implemented features

**Structure:**
```
docs/product/unimplemented/
├── README.md                          # Overview of unimplemented features
├── heat_map_visualization.md         # Heat map visualization feature
├── real_time_data_integration.md     # Yahoo Finance integration
├── transaction_details_tracking.md   # Detailed transaction tracking
├── position_change_logging.md        # Position change logging
└── enhanced_trade_event_logging.md   # Verbose event logging for traders
```

**Content Template for Each Feature:**
- Status: Planned / In Progress / Blocked
- Priority: High / Medium / Low
- Dependencies: What needs to be done first
- Specification: What the feature should do
- Implementation Notes: Technical considerations
- Related Issues/PRs: Links to tracking

---

## 🔄 Implementation Status

### Current Status (2025-01-27)

**✅ Implemented:**
- Core trading system
- Portfolio management
- Position management
- Order execution
- Simulation/backtesting
- Parameter optimization (Phase 1 complete)
- Excel export
- Audit trails

**⚠️ Partially Implemented:**
- Real-time data (mock data, Yahoo Finance integration missing)
- Heat map visualization (backend ready, frontend missing)

**❌ Not Implemented (Document in `docs/product/unimplemented/`):**
- Debug checkbox for export filtering
- Real-time Yahoo Finance integration
- Transaction details & event tracking
- Heat map visualization (frontend)
- Position change logging
- Enhanced verbose event logging for traders
- Multi-broker support

---

## 📋 Cleanup Checklist

### Phase 1: Create Structure
- [x] Create cleanup plan document
- [ ] Create `docs/archive/` directories
- [ ] Create `docs/product/unimplemented/` directory
- [ ] Create unimplemented feature documentation

### Phase 2: Move Files
- [ ] Move completion reports to archive
- [ ] Move QA reports to archive
- [ ] Move migration reports to archive
- [ ] Move test files to appropriate locations
- [ ] Delete obsolete files

### Phase 3: Update Documentation
- [ ] Update main README.md
- [ ] Update docs/README.md
- [ ] Update docs/DOCUMENTATION_INDEX.md
- [ ] Create docs/product/unimplemented/README.md
- [ ] Update cross-references

### Phase 4: Verify
- [ ] Verify all links work
- [ ] Verify documentation is accessible
- [ ] Update .gitignore if needed
- [ ] Create summary document

---

## 🎯 Success Criteria

1. **New developer can find current documentation in < 5 minutes**
2. **Obsolete files are clearly archived, not cluttering root**
3. **Unimplemented features are clearly documented**
4. **Documentation structure is logical and maintainable**
5. **No broken links in main documentation**

---

## 📚 Related Documents

- [Documentation Index](DOCUMENTATION_INDEX.md)
- [Documentation Status](DOCUMENTATION_STATUS.md)
- [Onboarding Guide](ONBOARDING.md)

---

_Last updated: 2025-01-27_



