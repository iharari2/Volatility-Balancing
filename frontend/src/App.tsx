import { Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import PageLayout from './components/layout/PageLayout';
import { ConfigurationProvider } from './contexts/ConfigurationContext';
import { OptimizationProvider } from './contexts/OptimizationContext';
import { PortfolioProvider } from './contexts/PortfolioContext';
import { TenantPortfolioProvider } from './contexts/TenantPortfolioContext';

// New pages
import OverviewPage from './features/overview/OverviewPage';
import PortfolioListPage from './features/portfolios/PortfolioListPage';
import PortfolioOverviewPage from './features/portfolios/PortfolioOverviewPage';
import PositionsPage from './features/positions/PositionsPage';
import PositionsAndConfigPage from './features/positions/PositionsAndConfigPage';
import PositionDetailPage from './features/positions/PositionDetailPage';
// TradeScreenPage has been removed - use PositionCockpitPage instead
// TradingConsolePage has been removed - use TradeSelectionPage instead
import TradingConsolePage from './features/trading/TradingConsolePage';
import TradeCockpitPage from './features/trading/TradeCockpitPage';
import SimulationLabPage from './features/simulation/SimulationLabPage';
import AnalyticsPage from './features/analytics/AnalyticsPage';
import AuditTrailPage from './features/audit/AuditTrailPage';
import SettingsPage from './features/settings/SettingsPage';

// Legacy pages (temporary - for migration)
import PortfolioManagement from './pages/PortfolioManagement';
import Trading from './pages/Trading';
import Simulation from './pages/Simulation';
import NotFound from './pages/NotFound';

function App() {
  const [mode, setMode] = useState<'Live' | 'Simulation' | 'Sandbox'>('Live');

  return (
    <TenantPortfolioProvider>
      <PortfolioProvider>
        <ConfigurationProvider>
          <OptimizationProvider>
            <PageLayout mode={mode}>
              <Routes>
                {/* New routes */}
                <Route path="/" element={<OverviewPage />} />
                <Route path="/overview" element={<OverviewPage />} />
                <Route path="/portfolios" element={<PortfolioListPage />} />
                <Route path="/portfolios/:portfolioId" element={<PortfolioOverviewPage />} />
                <Route
                  path="/portfolios/:portfolioId/positions"
                  element={<PositionsAndConfigPage />}
                />
                <Route
                  path="/portfolios/:portfolioId/positions/:positionId"
                  element={<PositionDetailPage />}
                />
                <Route path="/positions" element={<PositionsAndConfigPage />} />
                <Route path="/positions-legacy" element={<PositionsPage />} />
                {/* Trading Console routes */}
                <Route path="/trading" element={<TradingConsolePage />} />
                <Route path="/trade" element={<TradeCockpitPage />} />
                <Route
                  path="/trade/:portfolioId/position/:positionId"
                  element={<TradeCockpitPage />}
                />
                {/* Legacy trade screen routes - QUARANTINED
                    Old TradeScreenPage has been replaced by PositionCockpitPage
                    These routes are kept for backward compatibility but should not be used
                    TODO: Remove these routes after migration period
                */}
                {/* <Route path="/portfolios/:portfolioId/trade-screen" element={<TradeScreenPage />} /> */}
                {/* <Route path="/trade-screen" element={<TradeScreenPage />} /> */}
                <Route path="/simulation" element={<SimulationLabPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/audit" element={<AuditTrailPage />} />
                <Route path="/settings" element={<SettingsPage />} />

                {/* Legacy routes (temporary) */}
                <Route path="/portfolio" element={<PortfolioManagement />} />
                <Route path="/trading-legacy" element={<Trading />} />
                <Route path="/simulation-legacy" element={<Simulation />} />

                {/* 404 catch-all route */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </PageLayout>
            <Toaster position="top-right" />
          </OptimizationProvider>
        </ConfigurationProvider>
      </PortfolioProvider>
    </TenantPortfolioProvider>
  );
}

export default App;
