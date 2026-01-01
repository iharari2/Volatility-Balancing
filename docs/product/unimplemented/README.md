# Unimplemented Features

**Purpose:** Documentation of planned but not yet implemented features  
**Last Updated:** 2025-01-27

---

## 📋 Overview

This directory contains specifications and plans for features that are documented but not yet implemented in the Volatility Balancing system. These documents serve as:

- **Reference** for future development
- **Specification** for implementation planning
- **Tracking** of planned enhancements

---

## 🎯 Status Legend

- **📋 Planned** - Feature is planned but not started
- **🚧 In Progress** - Feature is currently being developed
- **⏸️ Blocked** - Feature is blocked by dependencies
- **✅ Implemented** - Feature has been completed (move to main docs)

---

## 📚 Unimplemented Features

### High Priority

1. **[Real-time Data Integration](real_time_data_integration.md)** 📋
   - Yahoo Finance integration for live market data
   - Currently using mock data
   - Status: Planned

2. **[Enhanced Trade Event Logging](enhanced_trade_event_logging.md)** 📋
   - Verbose chronological event log for traders
   - Full details: market data, triggers, thresholds, actions, results
   - Status: Planned (per UX feedback)

3. **[Transaction Details & Event Tracking](transaction_details_tracking.md)** 📋
   - Detailed transaction tracking per position
   - Open orders tracking (market price, bid/asks)
   - Key events (ex-dividend, market open/close)
   - Status: Planned

### Medium Priority

4. **[Heat Map Visualization](heat_map_visualization.md)** 🚧
   - Interactive heat map component for parameter analysis
   - Parameter sensitivity visualization
   - Backend ready, frontend missing
   - Status: Partially Implemented (backend complete)

5. **[Position Change Logging](position_change_logging.md)** 📋
   - Simple change logging system
   - Automatic log entry creation on position changes
   - Status: Planned

6. **[Debug Checkbox for Export Filtering](debug_export_filtering.md)** 📋
   - Checkbox to filter "all events" vs "successful transactions only"
   - Export frequency based on data granularity
   - Status: Planned

### Low Priority / Future Enhancements

7. **Multi-Broker Support** 📋
   - Support for multiple broker APIs
   - Broker-agnostic order execution
   - Status: Future Enhancement

8. **Advanced Analytics** 📋
   - Enhanced portfolio analytics
   - Advanced reporting features
   - Status: Future Enhancement

---

## 📝 Adding New Unimplemented Features

When documenting a new unimplemented feature:

1. Create a new markdown file in this directory
2. Use the template below
3. Update this README with the new feature
4. Link from relevant product specs or development plans

### Template

```markdown
# Feature Name

**Status:** Planned / In Progress / Blocked  
**Priority:** High / Medium / Low  
**Last Updated:** YYYY-MM-DD

## Overview

Brief description of the feature.

## Requirements

- Requirement 1
- Requirement 2

## Dependencies

- What needs to be done first
- Blocking issues

## Implementation Notes

Technical considerations and approach.

## Related Documents

- Links to related specs, issues, PRs
```

---

## 🔗 Related Documentation

- [Product Specification](../volatility_trading_spec_v1.md) - Main product spec
- [GUI Design Implementation Status](../../dev/gui_design_implementation_status.md) - Implementation status
- [Development Plan Status](../../dev/development_plan_status.md) - Overall project status
- [UX Implementation Plan](../../UX_IMPLEMENTATION_PLAN.md) - UX-related features

---

## 📊 Summary

| Feature | Priority | Status | Backend | Frontend |
|---------|----------|--------|---------|----------|
| Real-time Data Integration | High | Planned | ❌ | ❌ |
| Enhanced Trade Event Logging | High | Planned | ❌ | ❌ |
| Transaction Details Tracking | High | Planned | ❌ | ❌ |
| Heat Map Visualization | Medium | Partial | ✅ | ❌ |
| Position Change Logging | Medium | Planned | ❌ | ❌ |
| Debug Export Filtering | Medium | Planned | ❌ | ❌ |
| Multi-Broker Support | Low | Future | ❌ | ❌ |

---

_Last updated: 2025-01-27_



