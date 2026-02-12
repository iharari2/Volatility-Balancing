# How to See the New GUI Wireframes Implementation

## Quick Start

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies (if not already done):**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser and go to:**
   ```
   http://localhost:3000
   ```

5. **You should see:**
   - Top bar with Tenant/Portfolio selectors and Market status
   - Left sidebar with navigation menu
   - Overview page content

## What Was Implemented

### ✅ Global Layout (All Pages)
- **Top Bar**: Tenant selector ▼, Portfolio selector ▼, Market: OPEN/CLOSED indicator
- **Sidebar**: Navigation menu with all pages
- **Page Content**: Main content area on the right

### ✅ Overview Page (`/overview`)
- 4 Summary Cards: Total Value, Cash Balance, Stock %, P&L
- Asset Allocation Chart (pie/bar toggle)
- Recent Trades Table (last 10)
- Trigger & Guardrail Events Table
- Quick Action Buttons

### ✅ Portfolios Page (`/portfolios`)
- Portfolio list with values and auto-trading status
- "+ Create Portfolio" button
- 3-step creation wizard modal

### ✅ Positions & Config Page (`/positions`)
- Tabs: Positions | Cash & Limits | Strategy Config | Dividends
- Positions table
- Cash configuration form
- Strategy configuration form

### ✅ Trading Console (`/trading`)
- Trading state indicator
- Controls (Enable/Disable Auto Trading, Run Cycle, Pause/Resume)
- Last Cycle Summary
- Open Orders table
- Recent Executions table

### ✅ Settings Page (`/settings`)
- Tenant Defaults configuration
- System settings (Theme, Refresh Interval)

## Troubleshooting

### If you see a blank page:

1. **Check browser console (F12):**
   - Look for JavaScript errors
   - Check Network tab for failed requests

2. **Verify the dev server is running:**
   - You should see: `VITE vX.X.X ready in XXX ms`
   - URL should be: `http://localhost:3000`

3. **Check for TypeScript/compilation errors:**
   ```bash
   cd frontend
   npm run build
   ```

### If you see old pages:

1. **Clear browser cache:**
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Or clear cache in browser settings

2. **Verify you're using the correct routes:**
   - `/overview` - New Overview page
   - `/portfolios` - New Portfolios page
   - `/positions` - New Positions page
   - `/trading` - New Trading Console
   - `/settings` - New Settings page

### If components don't render:

1. **Check that backend is running:**
   - Backend should be on `http://localhost:8000`
   - Some features require backend API

2. **Verify all files exist:**
   ```bash
   ls frontend/src/features/overview/
   ls frontend/src/features/portfolios/
   ls frontend/src/features/settings/
   ```

3. **Check for missing imports:**
   - All components should be imported in `App.tsx`
   - All routes should be defined

## Expected Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│ TOP BAR: Tenant ▼  Portfolio ▼  Market: OPEN ▣  Settings ⚙ │
└─────────────────────────────────────────────────────────────┘
┌──────────┐ ┌───────────────────────────────────────────────┐
│ SIDEBAR  │ │ PAGE CONTENT                                  │
│          │ │                                               │
│ Overview │ │ [Summary Cards]                               │
│ Portfolios│ │ [Charts]                                     │
│ Positions│ │ [Tables]                                      │
│ Trading  │ │                                               │
│ ...      │ │                                               │
└──────────┘ └───────────────────────────────────────────────┘
```

## Next Steps

If you're still not seeing the new UI:

1. **Check the terminal output** when running `npm run dev`
2. **Look for error messages** in the browser console
3. **Try accessing a specific route directly**: `http://localhost:3000/overview`
4. **Verify all dependencies are installed**: `npm install`

## File Locations

All new components are in:
- `frontend/src/features/overview/` - Overview page components
- `frontend/src/features/portfolios/` - Portfolio components
- `frontend/src/features/trading/` - Trading console components
- `frontend/src/features/settings/` - Settings page
- `frontend/src/components/layout/` - Layout components (TopBar, Sidebar)
















