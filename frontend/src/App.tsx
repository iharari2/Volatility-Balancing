import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Positions from './pages/Positions';
import Trading from './pages/Trading';
import Simulation from './pages/Simulation';
import Analytics from './pages/Analytics';
import PositionDetail from './pages/PositionDetail';
import Optimization from './pages/Optimization';
import { ConfigurationProvider } from './contexts/ConfigurationContext';
import { OptimizationProvider } from './contexts/OptimizationContext';

function App() {
  return (
    <ConfigurationProvider>
      <OptimizationProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/positions" element={<Positions />} />
            <Route path="/positions/:id" element={<PositionDetail />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/optimization" element={<Optimization />} />
          </Routes>
        </Layout>
      </OptimizationProvider>
    </ConfigurationProvider>
  );
}

export default App;
