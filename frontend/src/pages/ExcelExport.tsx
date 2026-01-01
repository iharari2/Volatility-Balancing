import React, { useState, useEffect } from 'react';
import { Download, FileSpreadsheet, Loader2, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

interface ExportStatus {
  [key: string]: 'idle' | 'loading' | 'success' | 'error';
}

interface Simulation {
  id: string;
  ticker: string;
  start_date: string;
  end_date: string;
  created_at: string;
  metrics: {
    algorithm_return_pct: number;
    buy_hold_return_pct: number;
    excess_return: number;
    algorithm_trades: number;
  };
}

const ExcelExportPage: React.FC = () => {
  const [exportStatus, setExportStatus] = useState<ExportStatus>({});
  const [lastExport, setLastExport] = useState<string | null>(null);
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [selectedSimulation, setSelectedSimulation] = useState<string>('');
  const [isLoadingSimulations, setIsLoadingSimulations] = useState(false);

  const API_BASE = '/api/excel'; // Use proxy
  const SIMULATIONS_API = '/api/simulations'; // Use proxy

  // Load available simulations
  const loadSimulations = async () => {
    setIsLoadingSimulations(true);
    try {
      const response = await fetch(`${SIMULATIONS_API}/`);
      if (response.ok) {
        const data = await response.json();
        setSimulations(data.simulations || []);
        if (data.simulations && data.simulations.length > 0) {
          setSelectedSimulation(data.simulations[0].id);
        }
      } else {
        console.error('Failed to load simulations:', response.statusText);
        console.log('Response status:', response.status);
        console.log('Response text:', await response.text());
      }
    } catch (error) {
      console.error('Error loading simulations:', error);
    } finally {
      setIsLoadingSimulations(false);
    }
  };

  // Load simulations on component mount
  useEffect(() => {
    loadSimulations();
  }, []);

  const exportData = async (endpoint: string, exportName: string) => {
    setExportStatus((prev) => ({ ...prev, [exportName]: 'loading' }));

    try {
      const response = await fetch(`${API_BASE}${endpoint}`);

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${exportName}_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setExportStatus((prev) => ({ ...prev, [exportName]: 'success' }));
        setLastExport(exportName);

        // Reset status after 3 seconds
        setTimeout(() => {
          setExportStatus((prev) => ({ ...prev, [exportName]: 'idle' }));
        }, 3000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Export failed');
      }
    } catch (error) {
      console.error(`Export error for ${exportName}:`, error);
      setExportStatus((prev) => ({ ...prev, [exportName]: 'error' }));

      // Reset status after 5 seconds
      setTimeout(() => {
        setExportStatus((prev) => ({ ...prev, [exportName]: 'idle' }));
      }, 5000);
    }
  };

  const exportButtons = [
    {
      name: 'positions',
      label: 'Positions',
      description: 'Export all current positions with detailed information',
      endpoint: '/positions/export',
      icon: '📋',
      category: 'Trading Data',
    },
    {
      name: 'trades',
      label: 'Trades',
      description: 'Export complete trade history with execution details',
      endpoint: '/trades/export',
      icon: '🔄',
      category: 'Trading Data',
    },
    {
      name: 'orders',
      label: 'Orders',
      description: 'Export order history with status and execution info',
      endpoint: '/orders/export',
      icon: '📝',
      category: 'Trading Data',
    },
    {
      name: 'trading',
      label: 'Trading Data',
      description: 'Export all trading data in one comprehensive file',
      endpoint: '/trading/export',
      icon: '💼',
      category: 'Trading Data',
    },
    {
      name: 'simulation',
      label: 'Simulation Results',
      description: 'Export simulation results and performance metrics',
      endpoint: selectedSimulation
        ? `/simulations/${selectedSimulation}/export`
        : '/simulation/test-simulation/export',
      icon: '📊',
      category: 'Analysis',
      disabled: false, // Allow export even without selected simulation
    },
    {
      name: 'enhanced-simulation',
      label: 'Enhanced Simulation Report',
      description: 'Comprehensive simulation analysis with decision logs and audit trail',
      endpoint: selectedSimulation
        ? `/simulation/${selectedSimulation}/enhanced-export`
        : '/simulation/test-simulation/enhanced-export',
      icon: '🔍',
      category: 'Enhanced Analysis',
      disabled: false, // Allow export even without selected simulation
    },
    {
      name: 'enhanced-trading',
      label: 'Enhanced Trading Audit',
      description: 'Complete trading audit with comprehensive data logs and compliance analysis',
      endpoint: '/trading/enhanced-export',
      icon: '📋',
      category: 'Enhanced Analysis',
    },
    {
      name: 'optimization',
      label: 'Optimization Results',
      description: 'Export parameter optimization results and analysis',
      endpoint: '/optimization/test-config/export',
      icon: '📈',
      category: 'Analysis',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'loading':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileSpreadsheet className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'loading':
        return 'Exporting...';
      case 'success':
        return 'Exported!';
      case 'error':
        return 'Failed';
      default:
        return 'Export';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'loading':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'success':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'error':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const groupedExports = exportButtons.reduce((acc, button) => {
    if (!acc[button.category]) {
      acc[button.category] = [];
    }
    acc[button.category].push(button);
    return acc;
  }, {} as Record<string, typeof exportButtons>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Excel Export</h1>
        <p className="mt-2 text-gray-600">
          Export your data to Excel format for analysis and reporting
        </p>
      </div>

      {/* Simulation Selection */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Simulation</h2>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <select
              value={selectedSimulation}
              onChange={(e) => setSelectedSimulation(e.target.value)}
              disabled={isLoadingSimulations}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {simulations.length === 0 ? (
                <option value="">
                  {isLoadingSimulations ? 'Loading simulations...' : 'No simulations available'}
                </option>
              ) : (
                <>
                  <option value="">Select a simulation...</option>
                  {simulations.map((sim) => (
                    <option key={sim.id} value={sim.id}>
                      {sim.ticker} ({sim.start_date} to {sim.end_date}) -{' '}
                      {sim.metrics.algorithm_return_pct.toFixed(2)}% return
                    </option>
                  ))}
                </>
              )}
            </select>
          </div>
          <button
            onClick={loadSimulations}
            disabled={isLoadingSimulations}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoadingSimulations ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
        {simulations.length === 0 && !isLoadingSimulations && (
          <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              <strong>No simulations found in database.</strong> You can still export using test
              data or run a new simulation.
            </p>
            <p className="text-xs text-yellow-600 mt-1">
              The export buttons below will work with test data if no simulation is selected.
            </p>
            <div className="mt-2">
              <button
                onClick={() => window.open('/simulation', '_blank')}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
              >
                Run New Simulation
              </button>
            </div>
          </div>
        )}
      </div>

      {lastExport && (
        <div className="rounded-md bg-green-50 p-4 border border-green-200">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">
                Successfully exported {lastExport} data to Excel
              </p>
            </div>
          </div>
        </div>
      )}

      {Object.entries(groupedExports).map(([category, buttons]) => (
        <div key={category}>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">{category}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {buttons.map((button) => (
              <div
                key={button.name}
                className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow"
              >
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <span className="text-2xl">{button.icon}</span>
                    {button.label}
                  </h3>
                  <p className="text-sm text-gray-600 mt-2">{button.description}</p>
                </div>
                <div>
                  <button
                    onClick={() => exportData(button.endpoint, button.name)}
                    disabled={exportStatus[button.name] === 'loading' || button.disabled}
                    className={`w-full px-4 py-2 rounded-md font-medium transition-colors ${
                      exportStatus[button.name] === 'success'
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : button.disabled
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200 border border-gray-300'
                    } ${
                      exportStatus[button.name] === 'loading' ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <div className="flex items-center justify-center gap-2">
                      {getStatusIcon(exportStatus[button.name])}
                      {getStatusText(exportStatus[button.name])}
                    </div>
                  </button>

                  {exportStatus[button.name] !== 'idle' && (
                    <div
                      className={`mt-3 px-3 py-2 rounded-md border text-sm font-medium ${getStatusColor(
                        exportStatus[button.name],
                      )}`}
                    >
                      {exportStatus[button.name] === 'loading' && 'Exporting data...'}
                      {exportStatus[button.name] === 'success' && 'File downloaded successfully!'}
                      {exportStatus[button.name] === 'error' && 'Export failed. Please try again.'}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Export Tips</h3>
        <div className="text-blue-800">
          <ul className="space-y-2 text-sm">
            <li>
              • <strong>Positions:</strong> Export current portfolio positions with allocation
              details
            </li>
            <li>
              • <strong>Trades:</strong> Export complete trading history for analysis
            </li>
            <li>
              • <strong>Orders:</strong> Export order management and execution data
            </li>
            <li>
              • <strong>Simulation:</strong> Export backtest results and performance metrics
            </li>
            <li>
              • <strong>Optimization:</strong> Export parameter optimization results and analysis
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ExcelExportPage;
