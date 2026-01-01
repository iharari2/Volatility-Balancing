# Troubleshooting - Main Page Not Loading

## Common Issues

### 1. Missing Imports

**Fixed**: Added missing imports to `OverviewPage.tsx`:

- `useTenantPortfolio` from `../../contexts/TenantPortfolioContext`
- `marketHoursService, MarketStatus` from `../../services/marketHoursService`

### 2. Context Not Initialized

If the page shows "Please select a portfolio":

- The context is loading portfolios
- Check browser console for errors
- Navigate to `/portfolios` to select a portfolio

### 3. JavaScript Errors

Check browser console (F12) for:

- Import errors
- Context errors
- Runtime errors

### 4. CSS Not Loading

- Ensure Tailwind is configured correctly
- Check that `tailwind.config.js` includes the new component paths
- Verify `index.css` is imported in `main.tsx`

## Quick Fixes

1. **Clear browser cache** and reload
2. **Check browser console** for errors
3. **Verify all imports** are correct
4. **Check that dev server is running**: `npm run dev`

## Verification Steps

1. Open browser console (F12)
2. Check for any red error messages
3. Verify the page route: `http://localhost:5173/overview`
4. Check Network tab for failed API requests

## If Page Shows "Please select a portfolio"

This is expected behavior if no portfolio is selected. To fix:

1. Navigate to `/portfolios`
2. Click on a portfolio to select it
3. Return to `/overview`

The context should auto-select the first portfolio, but if portfolios haven't loaded yet, you'll see this message.
















