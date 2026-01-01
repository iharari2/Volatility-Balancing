# Quick Start - Viewing the New GUI Wireframes

## Steps to See the New Implementation

1. **Start the Frontend Development Server:**
   ```bash
   cd frontend
   npm install  # If you haven't already
   npm run dev
   ```

2. **Open in Browser:**
   - Navigate to: `http://localhost:3000`
   - The app should automatically redirect to `/overview` (the Overview page)

3. **Navigate Through Pages:**
   - **Overview** (`/overview`) - Main dashboard with summary cards, charts, and recent activity
   - **Portfolios** (`/portfolios`) - Portfolio list with creation wizard
   - **Positions & Config** (`/positions`) - Position management with tabs
   - **Trading Console** (`/trading`) - Trading controls and cycle summary
   - **Simulation Lab** (`/simulation`) - Simulation interface
   - **Analytics & Reports** (`/analytics`) - Analytics dashboard
   - **Audit Trail** (`/audit`) - Event timeline
   - **Settings** (`/settings`) - System settings

## What You Should See

### Top Bar (All Pages)
- Tenant dropdown selector
- Portfolio dropdown selector  
- Market status indicator (OPEN/CLOSED)
- Settings icon

### Sidebar (All Pages)
- Overview
- Portfolios
- Positions & Config
- Trading Console
- Simulation Lab
- Analytics & Reports
- Audit Trail
- Settings

### Overview Page Features
- 4 Summary Cards: Total Value, Cash Balance, Stock %, P&L
- Asset Allocation Chart (pie/bar toggle)
- Recent Trades Table (last 10)
- Trigger & Guardrail Events Table
- Quick Action Buttons

### Portfolio Page Features
- Portfolio list with values and status
- "+ Create Portfolio" button
- 3-step creation wizard modal

## Troubleshooting

### If you see a blank page:
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for failed API calls

### If components don't render:
1. Make sure backend is running on port 8000
2. Check that all dependencies are installed: `npm install`
3. Clear browser cache and hard refresh (Ctrl+Shift+R)

### If you see old pages:
1. Make sure you're using the new routes (e.g., `/overview` not `/portfolio`)
2. Check that the dev server restarted after code changes

## Expected Behavior

- **Top Bar**: Should show tenant/portfolio selectors and market status
- **Sidebar**: Should be visible on the left with all navigation items
- **Content Area**: Should show the page content on the right
- **Responsive**: Sidebar collapses on mobile, menu button appears

## Next Steps

If you're still not seeing the new UI:
1. Check browser console for JavaScript errors
2. Verify the frontend is running on port 3000
3. Try accessing `http://localhost:3000/overview` directly
4. Check that all files were saved correctly
















