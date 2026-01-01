# Debug Checkbox for Export Filtering

**Status:** 📋 Planned  
**Priority:** Medium  
**Last Updated:** 2025-01-27

---

## Overview

Add a debug checkbox to export functionality that allows filtering between "all events" and "successful transactions only". Also implement export frequency based on data granularity.

---

## Current State

- **Backend:** Export functionality exists
- **Frontend:** Basic export without filtering options
- **Missing:** Debug filtering and granularity control

---

## Requirements

### Functional Requirements

1. **Debug Checkbox**
   - Toggle between "all events" and "successful transactions only"
   - Clear labeling and tooltips
   - Persist user preference

2. **Export Frequency Control**
   - Export frequency based on data granularity
   - Support for 6-minute intervals (as specified)
   - Configurable export intervals
   - Automatic frequency selection based on data

3. **Filter Options**
   - Filter by event type
   - Filter by transaction status
   - Filter by date range
   - Custom filter combinations

### Technical Requirements

- Efficient filtering
- Large dataset handling
- Export performance optimization

---

## Dependencies

- Existing export functionality
- Event/transaction data structure

---

## Implementation Notes

### Backend Changes

1. **Export Filtering**
   - Add filter parameters to export endpoints
   - Implement event type filtering
   - Implement status filtering

2. **Export Frequency**
   - Data granularity detection
   - Frequency-based export logic
   - Interval configuration

### Frontend Changes

1. **Export UI**
   - Add debug checkbox
   - Add frequency selection
   - Add filter options
   - Update export button behavior

2. **User Preferences**
   - Save filter preferences
   - Remember last used settings

---

## Related Documents

- [Excel Export Guide](../../../backend/EXCEL_EXPORT_GUIDE.md)
- [GUI Design Implementation Status](../../dev/gui_design_implementation_status.md)

---

## Acceptance Criteria

- [ ] Debug checkbox functional
- [ ] Filtering working correctly
- [ ] Export frequency control implemented
- [ ] Performance acceptable for large datasets
- [ ] User preferences saved

---

_Last updated: 2025-01-27_



