// =========================
// frontend/src/components/ExcelExportExample.tsx
// =========================

import React from 'react';
import ExcelExport from './ExcelExport';

/**
 * Example component showing how to integrate Excel export functionality
 * into different parts of the application
 */
const ExcelExportExample: React.FC = () => {
  return (
    <div className="space-y-8 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Excel Export Examples</h1>

      {/* Optimization Results Export */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Optimization Results Export</h2>
        <p className="text-gray-600 mb-4">
          Export parameter optimization results with comprehensive analysis including parameter
          sensitivity, performance metrics, and recommendations.
        </p>
        <ExcelExport
          configId="123e4567-e89b-12d3-a456-426614174000"
          dataType="optimization"
          title="Export Optimization Results"
          className="inline-block"
        />
      </div>

      {/* Simulation Results Export */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Simulation Results Export</h2>
        <p className="text-gray-600 mb-4">
          Export trading simulation results with performance analysis, trade logs, and risk metrics.
        </p>
        <ExcelExport
          simulationId="sim_aapl_2024_001"
          dataType="simulation"
          title="Export Simulation Results"
          className="inline-block"
        />
      </div>

      {/* Trading Data Export */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Trading Data Export</h2>
        <p className="text-gray-600 mb-4">
          Export complete trading data including positions, trades, and orders with compliance
          analysis.
        </p>
        <ExcelExport dataType="trading" title="Export Trading Data" className="inline-block" />
      </div>

      {/* Position-Specific Export */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Position-Specific Export</h2>
        <p className="text-gray-600 mb-4">
          Export data for a specific position including trade history and performance analysis.
        </p>
        <ExcelExport
          positionId="pos_aapl_001"
          dataType="position"
          title="Export Position Data"
          className="inline-block"
        />
      </div>

      {/* Usage Instructions */}
      <div className="bg-blue-50 p-6 rounded-lg">
        <h2 className="text-lg font-semibold text-blue-800 mb-4">Usage Instructions</h2>
        <div className="text-blue-700 space-y-2">
          <p>
            <strong>1. Click Export Button:</strong> Click any export button to download the Excel
            file
          </p>
          <p>
            <strong>2. Choose Format:</strong> Currently only Excel (.xlsx) format is supported
          </p>
          <p>
            <strong>3. Multiple Sheets:</strong> Each export includes multiple sheets with different
            analysis
          </p>
          <p>
            <strong>4. Professional Formatting:</strong> Reports include professional styling and
            conditional formatting
          </p>
        </div>
      </div>

      {/* Available Templates */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Available Export Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded border">
            <h3 className="font-semibold text-gray-700">Optimization Results</h3>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• Executive Summary</li>
              <li>• Detailed Results</li>
              <li>• Parameter Sensitivity</li>
              <li>• Performance Metrics</li>
              <li>• Heatmap Data</li>
              <li>• Recommendations</li>
            </ul>
          </div>

          <div className="bg-white p-4 rounded border">
            <h3 className="font-semibold text-gray-700">Simulation Results</h3>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• Executive Summary</li>
              <li>• Performance Analysis</li>
              <li>• Trade Analysis</li>
              <li>• Risk Analysis</li>
              <li>• Market Analysis</li>
            </ul>
          </div>

          <div className="bg-white p-4 rounded border">
            <h3 className="font-semibold text-gray-700">Trading Data</h3>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• Executive Summary</li>
              <li>• Positions Analysis</li>
              <li>• Trades Analysis</li>
              <li>• Orders Analysis</li>
              <li>• Compliance Analysis</li>
              <li>• Performance Attribution</li>
            </ul>
          </div>

          <div className="bg-white p-4 rounded border">
            <h3 className="font-semibold text-gray-700">Position Data</h3>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• Position Summary</li>
              <li>• Trade History</li>
              <li>• Order History</li>
              <li>• Performance Metrics</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExcelExportExample;
