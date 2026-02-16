import { Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import PageLayout from './components/layout/PageLayout';
import ErrorBoundary from './components/shared/ErrorBoundary';
import { ConfigurationProvider } from './contexts/ConfigurationContext';
import { OptimizationProvider } from './contexts/OptimizationContext';
import { PortfolioProvider } from './contexts/PortfolioContext';
import { TenantPortfolioProvider } from './contexts/TenantPortfolioContext';

// New Workspace (Master-Detail Layout)
import PositionWorkspacePage from './features/workspace/PositionWorkspacePage';

// Feature pages
import PortfolioListPage from './features/portfolios/PortfolioListPage';
import PortfolioOverviewPage from './features/portfolios/PortfolioOverviewPage';
import PositionsAndConfigPage from './features/positions/PositionsAndConfigPage';
import PositionDetailPage from './features/positions/PositionDetailPage';
import TradeCockpitPage from './features/trading/TradeCockpitPage';
import SimulationLabPage from './features/simulation/SimulationLabPage';
import AnalyticsPage from './features/analytics/AnalyticsPage';
import MonitoringPage from './features/monitoring/MonitoringPage';
import OptimizationPage from './features/optimization/OptimizationPage';
import SettingsPage from './features/settings/SettingsPage';
import NotFound from './pages/NotFound';

function App() {
  const [mode, setMode] = useState<'Live' | 'Simulation' | 'Sandbox'>('Live');

  return (
    <TenantPortfolioProvider>
      <PortfolioProvider>
        <ConfigurationProvider>
          <OptimizationProvider>
            <ErrorBoundary>
            <Routes>
              {/* NEW: Position Workspace (Master-Detail Layout) - Default route */}
              <Route path="/" element={<PositionWorkspacePage />} />
              <Route path="/workspace" element={<PositionWorkspacePage />} />

              {/* Standalone pages with PageLayout */}
              <Route
                path="/simulation"
                element={
                  <PageLayout mode={mode}>
                    <SimulationLabPage />
                  </PageLayout>
                }
              />
              <Route
                path="/settings"
                element={
                  <PageLayout mode={mode}>
                    <SettingsPage />
                  </PageLayout>
                }
              />

              {/* Redirects from old routes to workspace */}
              <Route path="/overview" element={<Navigate to="/" replace />} />
              <Route path="/trading" element={<Navigate to="/?tab=trading" replace />} />
              <Route path="/trade" element={<Navigate to="/?tab=trading" replace />} />
              <Route path="/positions" element={<Navigate to="/" replace />} />

              {/* Legacy routes with PageLayout (kept for transition) */}
              <Route
                path="/portfolios"
                element={
                  <PageLayout mode={mode}>
                    <PortfolioListPage />
                  </PageLayout>
                }
              />
              <Route
                path="/portfolios/:portfolioId"
                element={
                  <PageLayout mode={mode}>
                    <PortfolioOverviewPage />
                  </PageLayout>
                }
              />
              <Route
                path="/portfolios/:portfolioId/positions"
                element={
                  <PageLayout mode={mode}>
                    <PositionsAndConfigPage />
                  </PageLayout>
                }
              />
              <Route
                path="/portfolios/:portfolioId/positions/:positionId"
                element={
                  <PageLayout mode={mode}>
                    <PositionDetailPage />
                  </PageLayout>
                }
              />
              <Route
                path="/trade/:portfolioId/position/:positionId"
                element={
                  <PageLayout mode={mode}>
                    <TradeCockpitPage />
                  </PageLayout>
                }
              />
              <Route
                path="/analytics"
                element={
                  <PageLayout mode={mode}>
                    <AnalyticsPage />
                  </PageLayout>
                }
              />
              <Route
                path="/monitoring"
                element={
                  <PageLayout mode={mode}>
                    <MonitoringPage />
                  </PageLayout>
                }
              />
              <Route
                path="/optimization"
                element={
                  <PageLayout mode={mode}>
                    <OptimizationPage />
                  </PageLayout>
                }
              />

              {/* 404 catch-all route */}
              <Route path="*" element={<NotFound />} />
            </Routes>
            </ErrorBoundary>
            <Toaster position="top-right" />
          </OptimizationProvider>
        </ConfigurationProvider>
      </PortfolioProvider>
    </TenantPortfolioProvider>
  );
}

export default App;
