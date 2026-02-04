import { useState } from 'react';
import { Play, Download, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { usePortfolio } from '../../contexts/PortfolioContext';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import SimulationResults from './SimulationResults';
import SimulationSetup from './SimulationSetup';
import { simulationApi } from '../../lib/api';

export default function SimulationLabPage() {
  const { selectedPortfolio } = useTenantPortfolio();
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunSimulation = async (config: any) => {
    setIsRunning(true);
    setError(null);
    setSimulationResult(null);

    try {
      // Validate config
      if (!config.asset || !config.startDate || !config.endDate) {
        throw new Error('Please fill in all required fields: Asset, Start Date, and End Date');
      }

      const resolutionToMinutes: Record<string, number> = {
        '1min': 1,
        '5min': 5,
        '15min': 15,
        '30min': 30,
        '1hour': 60,
        daily: 1440,
      };
      const intradayIntervalMinutes = resolutionToMinutes[config.resolution] || 30;

      // Validate and parse dates with comprehensive error handling
      const parseDate = (dateString: string, fieldName: string): Date => {
        if (!dateString || dateString.trim() === '') {
          throw new Error(`${fieldName} is required`);
        }

        let normalizedDate: string = dateString.trim();
        let parsedDate: Date;

        // Remove time portion if present
        if (normalizedDate.includes('T')) {
          normalizedDate = normalizedDate.split('T')[0];
        }

        // Check if it's in YYYY-MM-DD format (HTML date input standard)
        if (/^\d{4}-\d{2}-\d{2}$/.test(normalizedDate)) {
          // Standard HTML date input format
          parsedDate = new Date(normalizedDate + 'T00:00:00.000Z');
        } else if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(normalizedDate)) {
          // MM/DD/YYYY format (common US format)
          const [month, day, year] = normalizedDate.split('/').map(Number);
          if (month < 1 || month > 12) {
            throw new Error(
              `Invalid ${fieldName} format: "${dateString}". Month must be between 1 and 12.`,
            );
          }
          if (day < 1 || day > 31) {
            throw new Error(
              `Invalid ${fieldName} format: "${dateString}". Day must be between 1 and 31.`,
            );
          }
          // Create date in YYYY-MM-DD format
          const yearStr = year.toString().padStart(4, '0');
          const monthStr = month.toString().padStart(2, '0');
          const dayStr = day.toString().padStart(2, '0');
          normalizedDate = `${yearStr}-${monthStr}-${dayStr}`;
          parsedDate = new Date(normalizedDate + 'T00:00:00.000Z');
        } else {
          // Try to parse as-is (might be other format)
          parsedDate = new Date(normalizedDate);
          if (isNaN(parsedDate.getTime())) {
            throw new Error(
              `Invalid ${fieldName} format: "${dateString}". Please use YYYY-MM-DD (e.g., 2024-12-21) or MM/DD/YYYY (e.g., 12/21/2024) format.`,
            );
          }
          // Normalize to YYYY-MM-DD
          normalizedDate = parsedDate.toISOString().split('T')[0];
        }

        // Validate the date is actually valid
        if (isNaN(parsedDate.getTime())) {
          throw new Error(
            `Invalid ${fieldName}: "${dateString}". The date "${normalizedDate}" is not a valid calendar date.`,
          );
        }

        // Extract components for validation
        const year = parsedDate.getUTCFullYear();
        const month = parsedDate.getUTCMonth() + 1;
        const day = parsedDate.getUTCDate();

        // Validate year range
        if (year < 1900 || year > 2100) {
          throw new Error(
            `Invalid year in ${fieldName}: ${year}. Year must be between 1900 and 2100.`,
          );
        }

        return parsedDate;
      };

      let startDate: Date;
      let endDateInput: Date;
      try {
        startDate = parseDate(config.startDate, 'Start date');
        endDateInput = parseDate(config.endDate, 'End date');
      } catch (error: any) {
        throw new Error(error.message || 'Invalid date format');
      }

      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

      // Use UTC methods for consistent date comparison
      const startYear = startDate.getUTCFullYear();
      const startMonth = startDate.getUTCMonth();
      const startDay = startDate.getUTCDate();
      const startDateDay = new Date(Date.UTC(startYear, startMonth, startDay));

      const endYear = endDateInput.getUTCFullYear();
      const endMonth = endDateInput.getUTCMonth();
      const endDay = endDateInput.getUTCDate();
      const endDateInputDay = new Date(Date.UTC(endYear, endMonth, endDay));

      const currentYear = now.getFullYear();
      const todayUTC = new Date(Date.UTC(now.getFullYear(), now.getUTCMonth(), now.getUTCDate()));

      // Check if dates are in the future BEFORE processing
      if (startYear > currentYear) {
        throw new Error(
          `Start date "${
            config.startDate
          }" is in the future (year ${startYear}). Simulations require historical data, so dates must be in the past. Please select a date in ${currentYear} or earlier. Today is ${
            today.toISOString().split('T')[0]
          }.`,
        );
      }
      if (startDateDay > todayUTC) {
        throw new Error(
          `Start date "${
            config.startDate
          }" is in the future. Simulations require historical data, so dates must be in the past. Please select a date on or before today (${
            today.toISOString().split('T')[0]
          }).`,
        );
      }

      if (endYear > currentYear) {
        throw new Error(
          `End date "${
            config.endDate
          }" is in the future (year ${endYear}). Simulations require historical data, so dates must be in the past. Please select a date in ${currentYear} or earlier. Today is ${
            today.toISOString().split('T')[0]
          }.`,
        );
      }
      if (endDateInputDay > todayUTC) {
        throw new Error(
          `End date "${
            config.endDate
          }" is in the future. Simulations require historical data, so dates must be in the past. Please select a date on or before today (${
            today.toISOString().split('T')[0]
          }).`,
        );
      }

      // If end date is today, use current time; otherwise use end of day
      let endDate: Date;
      if (endDateInputDay.getTime() === todayUTC.getTime()) {
        // End date is today - use current time
        endDate = now;
      } else {
        // End date is in the past - use end of that day
        // Use the normalized date from parsing
        const endDateStr = endDateInput.toISOString().split('T')[0];
        endDate = new Date(endDateStr + 'T23:59:59.999Z');
        if (isNaN(endDate.getTime())) {
          throw new Error(`Failed to create end date from: ${config.endDate}`);
        }
      }

      // Validate date range
      if (startDate >= endDate) {
        throw new Error(
          `Start date (${config.startDate}) must be before end date (${config.endDate}).`,
        );
      }

      // Final validation before creating ISO strings
      if (isNaN(startDate.getTime())) {
        throw new Error(
          `Invalid start date: "${config.startDate}". Please enter a valid date in YYYY-MM-DD format.`,
        );
      }
      if (isNaN(endDate.getTime())) {
        throw new Error(
          `Invalid end date: "${config.endDate}". Please enter a valid date in YYYY-MM-DD format.`,
        );
      }

      // Safely convert to ISO strings
      let startDateISO: string;
      let endDateISO: string;
      try {
        startDateISO = startDate.toISOString();
        endDateISO = endDate.toISOString();
      } catch (isoError: any) {
        throw new Error(
          `Failed to convert dates to ISO format. Start: "${config.startDate}", End: "${config.endDate}". Please check that both dates are valid and not in the future.`,
        );
      }

      // Build position_config with user-defined trigger threshold
      const triggerThresholdDecimal = (config.triggerThresholdPct || 3) / 100; // Convert 3% to 0.03
      const positionConfig = {
        trigger_threshold_pct: triggerThresholdDecimal,
        rebalance_ratio: 1.6667,
        commission_rate: 0.0001,
        min_notional: 100.0,
        allow_after_hours: config.allowAfterHours ?? true,
        guardrails: {
          min_stock_alloc_pct: 0.25,
          max_stock_alloc_pct: 0.75,
        },
      };

      const request = {
        ticker: config.asset.toUpperCase().trim(),
        start_date: startDateISO,
        end_date: endDateISO,
        initial_cash: config.initialCash || 10000,
        include_after_hours: config.allowAfterHours ?? false,
        intraday_interval_minutes: intradayIntervalMinutes,
        position_config: positionConfig,
        comparison_ticker: config.comparisonTicker?.toUpperCase().trim() || null,
      };

      console.log('Running simulation with config:', request);
      const result = await simulationApi.runSimulation(request);
      console.log('Simulation completed:', result);

      // If comparison ticker is specified but not returned by backend, fetch it separately
      if (config.comparisonTicker && !result.comparison_data) {
        try {
          const comparisonResponse = await fetch(
            `/api/v1/market/historical/${config.comparisonTicker.toUpperCase().trim()}?start_date=${startDateISO}&end_date=${endDateISO}`
          );
          if (comparisonResponse.ok) {
            const comparisonData = await comparisonResponse.json();
            if (comparisonData.price_data && comparisonData.price_data.length > 0) {
              const firstPrice = comparisonData.price_data[0].price;
              result.comparison_ticker = config.comparisonTicker.toUpperCase().trim();
              result.comparison_data = comparisonData.price_data.map((d: any) => ({
                date: d.timestamp.split('T')[0],
                price: d.price,
                normalized_return: ((d.price - firstPrice) / firstPrice) * 100,
              }));
            }
          }
        } catch (err) {
          console.warn('Could not fetch comparison ticker data:', err);
        }
      }

      setSimulationResult(result);
      setIsRunning(false);
    } catch (error: any) {
      console.error('Simulation failed:', error);
      // Provide a more user-friendly error message
      let errorMessage = 'Unknown error occurred. Please check the console for details.';

      if (error?.message) {
        errorMessage = error.message;
      } else if (error?.detail) {
        errorMessage = error.detail;
      } else if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }

      setError(errorMessage);
      setIsRunning(false);
    }
  };

  if (!selectedPortfolio) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">Please select a portfolio to run simulations</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Workspace
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Simulation Lab</h1>
          <p className="text-sm text-gray-500 mt-1">{selectedPortfolio.name}</p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">Simulation Error</h3>
              <p className="mt-1 text-sm text-red-700 whitespace-pre-line">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Simulation Setup */}
        <div className="lg:col-span-1">
          <SimulationSetup onRun={handleRunSimulation} isRunning={isRunning} />
        </div>

        {/* Right Panel - Results */}
        <div className="lg:col-span-1">
          <SimulationResults result={simulationResult} />
        </div>
      </div>
    </div>
  );
}







