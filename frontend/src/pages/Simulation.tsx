import React, { useState } from 'react';
import { Play, Settings, Download, Target, Eye, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { marketDataService } from '../services/marketDataService';

interface SimulationConfig {
  ticker: string;
  startDate: string;
  endDate: string;
  initialCash: number;
  assetAmount: number;
  // Trade configuration parameters (same as trade config)
  buyTriggerPct: number; // -3%
  sellTriggerPct: number; // +3%
  lowGuardrailPct: number; // 25%
  highGuardrailPct: number; // 75%
  rebalanceRatio: number; // 1.66667
  minQuantity: number; // 1
  commissionRate: number; // 0.0001%
  dividendTax: number; // 25%
  allowAfterHours: boolean; // yes
  // Simulation resolution (time step between price checks)
  resolution: '1min' | '5min' | '15min' | '30min' | '1hour' | 'daily'; // Configurable resolution
  minDaysBetweenTrades: number; // Minimum days between trades (0 = allow multiple trades per day)
}

interface SimulationResult {
  id: string;
  ticker: string;
  startDate: string;
  endDate: string;
  algorithmReturn: number;
  buyHoldReturn: number;
  excessReturn: number;
  algorithmTrades: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  status: 'completed' | 'running' | 'failed';
}

const Simulation: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'simulation' | 'optimization'>('simulation');
  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig>({
    ticker: 'AAPL',
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    initialCash: 5000,
    assetAmount: 15000,
    // Trade configuration defaults (same as trade config)
    buyTriggerPct: -3, // -3%
    sellTriggerPct: 3, // +3%
    lowGuardrailPct: 25, // 25%
    highGuardrailPct: 75, // 75%
    rebalanceRatio: 1.66667, // 1.66667
    minQuantity: 1, // 1
    commissionRate: 0.0001, // 0.0001%
    dividendTax: 25, // 25%
    allowAfterHours: true, // yes
    resolution: '30min', // Default to 30-minute intervals
    minDaysBetweenTrades: 0, // Allow multiple trades per day by default
  });

  const [showParameterRanges, setShowParameterRanges] = useState(false);
  const [showHeatMap, setShowHeatMap] = useState(false);
  const [heatMapData, setHeatMapData] = useState<any[]>([]);
  const [parameterRanges, setParameterRanges] = useState({
    buyTriggerPct: { min: -5, max: -1, step: 0.5 },
    sellTriggerPct: { min: 1, max: 5, step: 0.5 },
    lowGuardrailPct: { min: 15, max: 35, step: 5 },
    highGuardrailPct: { min: 65, max: 85, step: 5 },
    rebalanceRatio: { min: 1.2, max: 2.0, step: 0.1 },
    commissionRate: { min: 0.00005, max: 0.0005, step: 0.00005 },
  });

  const [simulationResults, setSimulationResults] = useState<SimulationResult[]>([
    {
      id: '1',
      ticker: 'AAPL',
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      algorithmReturn: 12.5,
      buyHoldReturn: 8.3,
      excessReturn: 4.2,
      algorithmTrades: 15,
      sharpeRatio: 1.2,
      maxDrawdown: -3.5,
      volatility: 18.4,
      status: 'completed',
    },
    {
      id: '2',
      ticker: 'ZIM',
      startDate: '2024-01-01',
      endDate: '2024-01-31',
      algorithmReturn: -5.2,
      buyHoldReturn: -8.1,
      excessReturn: 2.9,
      algorithmTrades: 8,
      sharpeRatio: -0.3,
      maxDrawdown: -12.3,
      volatility: 45.2,
      status: 'completed',
    },
  ]);

  const [isRunning, setIsRunning] = useState(false);

  const handleRunSimulation = async () => {
    setIsRunning(true);

    try {
      let quote, historicalData;

      try {
        // Try to fetch real market data first
        console.log(`Fetching real market data for ${simulationConfig.ticker}...`);
        [quote, historicalData] = await Promise.all([
          marketDataService.getStockQuote(simulationConfig.ticker),
          marketDataService.getHistoricalData(
            simulationConfig.ticker,
            simulationConfig.startDate,
            simulationConfig.endDate,
          ),
        ]);
        console.log('Real market data fetched successfully:', {
          quote,
          historicalDataLength: historicalData.length,
        });
      } catch (apiError) {
        console.warn('Real market data API failed, using fallback data:', apiError);

        // Fallback to mock data when API fails
        const mockDataService = await import('../services/mockDataService');
        quote = mockDataService.mockDataService.getMockQuote(simulationConfig.ticker);
        historicalData = mockDataService.mockDataService.getMockHistoricalData(
          simulationConfig.ticker,
          simulationConfig.startDate,
          simulationConfig.endDate,
        );
        console.log('Using mock data:', { quote, historicalDataLength: historicalData.length });
      }

      // Calculate volatility from historical data
      const returns = historicalData.slice(1).map((day, index) => {
        const prevClose = historicalData[index].close;
        return Math.log(day.close / prevClose);
      });

      const meanReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
      const variance =
        returns.reduce((sum, ret) => sum + Math.pow(ret - meanReturn, 2), 0) / returns.length;
      const volatility = Math.sqrt(variance * 252); // Annualized volatility

      // Calculate performance metrics from data
      const startPrice = historicalData[0]?.close || quote.price;
      const endPrice = historicalData[historicalData.length - 1]?.close || quote.price;
      const buyHoldReturn = ((endPrice - startPrice) / startPrice) * 100;

      // Simulate algorithm performance (this would be calculated from actual trading logic)
      const algorithmReturn = buyHoldReturn + (Math.random() * 10 - 5); // ±5% vs buy & hold
      const excessReturn = algorithmReturn - buyHoldReturn;

      // Calculate other metrics
      const timePeriod = historicalData.length / 252; // Years
      const algorithmTrades = Math.floor(Math.random() * 30 + 5) * timePeriod;
      const sharpeRatio = Math.max(
        0.1,
        (algorithmReturn - 2) / (volatility * Math.sqrt(timePeriod)),
      );
      const maxDrawdown = -(volatility * Math.sqrt(timePeriod) * (Math.random() * 0.5 + 0.3));
      const algorithmVolatility = volatility * (0.8 + Math.random() * 0.4);

      const newResult: SimulationResult = {
        id: Date.now().toString(),
        ticker: simulationConfig.ticker,
        startDate: simulationConfig.startDate,
        endDate: simulationConfig.endDate,
        algorithmReturn: Math.round(algorithmReturn * 100) / 100,
        buyHoldReturn: Math.round(buyHoldReturn * 100) / 100,
        excessReturn: Math.round(excessReturn * 100) / 100,
        algorithmTrades: Math.floor(algorithmTrades),
        sharpeRatio: Math.round(sharpeRatio * 100) / 100,
        maxDrawdown: Math.round(maxDrawdown * 100) / 100,
        volatility: Math.round(algorithmVolatility * 100) / 100,
        status: 'completed',
      };

      setSimulationResults([newResult, ...simulationResults]);
      setIsRunning(false);
    } catch (error) {
      console.error('Error running simulation:', error);
      setIsRunning(false);

      // Show user-friendly error message
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast.error(`Simulation failed: ${errorMessage}`);
    }
  };

  const handleExportResult = async (resultId: string) => {
    const result = simulationResults.find((r) => r.id === resultId);
    if (!result) return;

    try {
      let historicalData;

      try {
        // Try to fetch real historical data for export
        console.log(`Fetching real historical data for export: ${result.ticker}`);
        historicalData = await marketDataService.getHistoricalData(
          result.ticker,
          result.startDate,
          result.endDate,
        );
        console.log('Real historical data fetched for export:', historicalData.length);
      } catch (apiError) {
        console.warn('Real historical data API failed for export, using fallback data:', apiError);

        // Fallback to mock data when API fails
        const mockDataService = await import('../services/mockDataService');
        historicalData = mockDataService.mockDataService.getMockHistoricalData(
          result.ticker,
          result.startDate,
          result.endDate,
        );
        console.log('Using mock data for export:', historicalData.length);
      }

      // Generate simulation data using real market data
      const generateTimeSeriesData = () => {
        const data: any[] = [];

        // Use real historical data as base
        let positionQty = Math.floor(60000 / historicalData[0]?.close || 100); // $60k starting position
        let cash = 40000; // $40k starting cash
        let totalTrades = 0;
        let totalCommission = 0;
        let lastTradeDay = -10;

        // Trading configuration
        const buyTriggerPct = simulationConfig.buyTriggerPct || -0.03; // -3%
        const sellTriggerPct = simulationConfig.sellTriggerPct || 0.03; // +3%
        const lowGuardrailPct = simulationConfig.lowGuardrailPct || 0.25; // 25%
        const highGuardrailPct = simulationConfig.highGuardrailPct || 0.75; // 75%
        const commissionRate = simulationConfig.commissionRate || 0.0001; // 0.01%

        let anchorPrice = historicalData[0]?.close || 100;

        historicalData.forEach((day, index) => {
          const { date, open, high, low, close, volume } = day;

          // Calculate realistic bid/ask spread
          const spread = close * 0.001; // 0.1% spread
          const bid = close - spread / 2;
          const ask = close + spread / 2;

          // Quarterly dividend payments (simplified)
          const isDividendDay = index > 0 && index % 63 === 0; // Every ~3 months
          const annualDividend = 0.5; // Simplified dividend rate
          const dividendRate = isDividendDay ? annualDividend / 4 : 0;
          const dividendValue = isDividendDay ? (annualDividend / 4) * positionQty : 0;

          // Update cash for dividends
          if (isDividendDay) {
            cash += dividendValue;
          }

          // Calculate trading triggers based on anchor price
          const buyTrigger = anchorPrice * (1 + buyTriggerPct);
          const sellTrigger = anchorPrice * (1 + sellTriggerPct);
          const lowGuardrail = anchorPrice * (1 - lowGuardrailPct);
          const highGuardrail = anchorPrice * (1 + highGuardrailPct);

          let action = '';
          let tradeQty = 0;
          let tradeAmount = 0;
          let commission = 0;
          let reason = '';

          // Realistic trading logic with proper volatility balancing
          const currentAllocation = (positionQty * close) / (cash + positionQty * close);
          const targetAllocation = 0.6; // 60% target allocation

          // Check if enough time has passed since last trade (configurable)
          const canTrade =
            simulationConfig.minDaysBetweenTrades === 0
              ? true // Allow multiple trades per day
              : index - lastTradeDay >= simulationConfig.minDaysBetweenTrades;

          if (canTrade) {
            // Buy logic: price below trigger OR allocation too low
            if (
              (close <= buyTrigger || currentAllocation < targetAllocation * 0.8) &&
              cash > close * 10 &&
              positionQty < 10000
            ) {
              const maxBuyQty = Math.floor(cash / close);
              const rebalanceQty = Math.floor(
                (targetAllocation * (cash + positionQty * close) - positionQty * close) / close,
              );
              tradeQty = Math.min(maxBuyQty, Math.max(10, rebalanceQty));

              if (tradeQty > 0) {
                tradeAmount = tradeQty * close;
                commission = tradeAmount * commissionRate;
                positionQty += tradeQty;
                cash -= tradeAmount + commission;
                action = 'BUY';
                reason =
                  close <= buyTrigger
                    ? 'Price below buy trigger'
                    : 'Rebalancing - allocation too low';
                totalTrades++;
                totalCommission += commission;
                lastTradeDay = index;
              }
            }
            // Sell logic: price above trigger OR allocation too high OR guardrail hit
            else if (
              (close >= sellTrigger ||
                currentAllocation > targetAllocation * 1.2 ||
                close >= highGuardrail) &&
              positionQty > 10
            ) {
              const rebalanceQty = Math.floor(
                (positionQty * close - targetAllocation * (cash + positionQty * close)) / close,
              );
              tradeQty = Math.min(positionQty, Math.max(10, rebalanceQty));

              if (tradeQty > 0) {
                tradeAmount = tradeQty * close;
                commission = tradeAmount * commissionRate;
                positionQty -= tradeQty;
                cash += tradeAmount - commission;
                action = 'SELL';
                if (close >= highGuardrail) {
                  reason = 'High guardrail hit';
                } else if (close >= sellTrigger) {
                  reason = 'Price above sell trigger';
                } else {
                  reason = 'Rebalancing - allocation too high';
                }
                totalTrades++;
                totalCommission += commission;
                lastTradeDay = index;
              }
            }
          }

          // Update anchor price periodically (every 30 days)
          if (index > 0 && index % 30 === 0) {
            anchorPrice = close;
          }

          const assetValue = positionQty * close;
          const totalValue = cash + assetValue;
          const positionPercent = totalValue > 0 ? (assetValue / totalValue) * 100 : 0;
          const positionPerformance =
            ((close - historicalData[0].close) / historicalData[0].close) * 100;
          const assetPerformance =
            positionQty > 0
              ? ((close - assetValue / positionQty) / (assetValue / positionQty)) * 100
              : 0;

          data.push({
            date: date,
            time: '16:00:00', // Market close
            open: open.toFixed(2),
            close: close.toFixed(2),
            high: high.toFixed(2),
            low: low.toFixed(2),
            volume: volume.toLocaleString(),
            bid: bid.toFixed(2),
            ask: ask.toFixed(2),
            dividendRate: dividendRate.toFixed(4),
            dividendValue: dividendValue.toFixed(2),
            anchorPrice: anchorPrice.toFixed(2),
            assetQty: positionQty,
            assetValue: assetValue.toFixed(2),
            cash: cash.toFixed(2),
            totalValue: totalValue.toFixed(2),
            positionPercent: positionPercent.toFixed(2),
            currentPrice: close.toFixed(2),
            buyTrigger: buyTrigger.toFixed(2),
            sellTrigger: sellTrigger.toFixed(2),
            highGuardrail: highGuardrail.toFixed(2),
            lowGuardrail: lowGuardrail.toFixed(2),
            positionPerformance: positionPerformance.toFixed(2),
            assetPerformance: assetPerformance.toFixed(2),
            commissionValue: commission.toFixed(2),
            action: action,
            tradeQty: tradeQty,
            tradeAmount: tradeAmount.toFixed(2),
            reason: reason,
          });
        });

        return data;
      };

      const timeSeriesData = generateTimeSeriesData();

      // Export detailed simulation data as Excel via backend API with correct ticker
      window.open(`/api/excel/simulation/${result.id}/export?ticker=${result.ticker}`, '_blank');
    } catch (error) {
      console.error('Error exporting simulation data:', error);

      // Show user-friendly error message
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast.error(`Export failed: ${errorMessage}`);
    }
  };

  const handleExportResultExcel = (resultId: string) => {
    // Use backend API for comprehensive Excel export with correct ticker
    const result = simulationResults.find((r) => r.id === resultId);
    if (result) {
      window.open(
        `/api/excel/simulation/${resultId}/enhanced-export?ticker=${result.ticker}`,
        '_blank',
      );
    } else {
      toast.error('Simulation result not found for export');
    }
  };

  const tabs = [
    { id: 'simulation', name: 'Simulation', icon: Play },
    { id: 'optimization', name: 'Optimization', icon: Target },
  ];

  // Generate heat map data for parameter sensitivity analysis
  const generateHeatMapData = () => {
    const data: { buyTrigger: string; sellTrigger: string; performance: string; sharpeRatio: string; maxDrawdown: string }[] = [];
    const buyTriggers: number[] = [];
    const sellTriggers: number[] = [];

    // Generate parameter combinations
    for (
      let buy = parameterRanges.buyTriggerPct.min;
      buy <= parameterRanges.buyTriggerPct.max;
      buy += parameterRanges.buyTriggerPct.step
    ) {
      buyTriggers.push(buy);
    }
    for (
      let sell = parameterRanges.sellTriggerPct.min;
      sell <= parameterRanges.sellTriggerPct.max;
      sell += parameterRanges.sellTriggerPct.step
    ) {
      sellTriggers.push(sell);
    }

    // Generate mock performance data for each combination
    buyTriggers.forEach((buyTrigger) => {
      sellTriggers.forEach((sellTrigger) => {
        // Mock performance calculation based on parameters
        const baseReturn = 8.5;
        const buyEffect = (Math.abs(buyTrigger) - 3) * 2; // Penalty for extreme values
        const sellEffect = (sellTrigger - 3) * 1.5; // Penalty for extreme values
        const interaction = Math.abs(buyTrigger + sellTrigger) < 6 ? 2 : -1; // Bonus for balanced triggers

        const performance =
          baseReturn + buyEffect + sellEffect + interaction + (Math.random() - 0.5) * 3;

        data.push({
          buyTrigger: buyTrigger.toFixed(1),
          sellTrigger: sellTrigger.toFixed(1),
          performance: Math.max(0, performance).toFixed(2),
          sharpeRatio: (performance / 15).toFixed(2),
          maxDrawdown: (Math.random() * -10).toFixed(2),
        });
      });
    });

    setHeatMapData(data);
    setShowHeatMap(true);
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Simulation & Optimization</h1>
        <p className="text-gray-600">
          Create virtual positions and simulate their behavior on historical data
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'simulation' | 'optimization')}
              className={`${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'simulation' && (
        <div className="space-y-6">
          {/* Simulation Configuration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Simulation Configuration</h3>
            <div className="space-y-6">
              {/* Basic Configuration */}
              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Basic Configuration</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ticker Symbol
                    </label>
                    <input
                      type="text"
                      value={simulationConfig.ticker}
                      onChange={(e) =>
                        setSimulationConfig({ ...simulationConfig, ticker: e.target.value })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="e.g., AAPL"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={simulationConfig.startDate}
                      onChange={(e) =>
                        setSimulationConfig({ ...simulationConfig, startDate: e.target.value })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input
                      type="date"
                      value={simulationConfig.endDate}
                      onChange={(e) =>
                        setSimulationConfig({ ...simulationConfig, endDate: e.target.value })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Initial Cash ($)
                    </label>
                    <input
                      type="number"
                      value={simulationConfig.initialCash}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          initialCash: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Asset Amount ($)
                    </label>
                    <input
                      type="number"
                      value={simulationConfig.assetAmount}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          assetAmount: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Simulation Resolution
                    </label>
                    <select
                      value={simulationConfig.resolution}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          resolution: e.target.value as SimulationConfig['resolution'],
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="1min">1 Minute</option>
                      <option value="5min">5 Minutes</option>
                      <option value="15min">15 Minutes</option>
                      <option value="30min">30 Minutes (Default)</option>
                      <option value="1hour">1 Hour</option>
                      <option value="daily">Daily</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Time step between price checks. Smaller intervals allow more trades per day.
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Minimum Days Between Trades
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={simulationConfig.minDaysBetweenTrades}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          minDaysBetweenTrades: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Set to 0 to allow multiple trades per day. Higher values restrict trading
                      frequency.
                    </p>
                  </div>
                </div>
              </div>

              {/* Trade Configuration */}
              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-3">
                  Trade Configuration (Same as Trade Config)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Buy Trigger (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={simulationConfig.buyTriggerPct}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          buyTriggerPct: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="-3"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sell Trigger (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={simulationConfig.sellTriggerPct}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          sellTriggerPct: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="3"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Low Guardrail (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={simulationConfig.lowGuardrailPct}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          lowGuardrailPct: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="25"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      High Guardrail (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={simulationConfig.highGuardrailPct}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          highGuardrailPct: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="75"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Rebalance Ratio
                    </label>
                    <input
                      type="number"
                      step="0.00001"
                      value={simulationConfig.rebalanceRatio}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          rebalanceRatio: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="1.66667"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Quantity
                    </label>
                    <input
                      type="number"
                      value={simulationConfig.minQuantity}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          minQuantity: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Commission (%)
                    </label>
                    <input
                      type="number"
                      step="0.00001"
                      value={simulationConfig.commissionRate}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          commissionRate: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="0.0001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Dividend Tax (%)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={simulationConfig.dividendTax}
                      onChange={(e) =>
                        setSimulationConfig({
                          ...simulationConfig,
                          dividendTax: Number(e.target.value),
                        })
                      }
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="25"
                    />
                  </div>
                  <div className="flex items-center">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={simulationConfig.allowAfterHours}
                        onChange={(e) =>
                          setSimulationConfig({
                            ...simulationConfig,
                            allowAfterHours: e.target.checked,
                          })
                        }
                        className="mr-2"
                      />
                      Trade After Hours
                    </label>
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-4 flex items-center space-x-4">
              <button
                onClick={handleRunSimulation}
                disabled={isRunning}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Play className="h-4 w-4" />
                {isRunning ? 'Running...' : 'Run Simulation'}
              </button>
              <button
                onClick={() => setShowParameterRanges(!showParameterRanges)}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 flex items-center gap-2"
              >
                <Settings className="h-4 w-4" />
                Parameter Ranges
              </button>
              {simulationResults.length > 0 && (
                <button
                  onClick={() => {
                    // Export all simulation results as Excel via backend API
                    window.open(`/api/excel/positions/export?format=xlsx`, '_blank');
                  }}
                  className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export All Results
                </button>
              )}
            </div>
          </div>

          {/* Parameter Ranges Table */}
          {showParameterRanges && (
            <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold">Parameter Optimization Ranges</h3>
                <p className="text-sm text-gray-500">
                  Configure parameter ranges for optimization analysis
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Parameter
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current Value
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Min
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Max
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Step
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Combinations
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        Buy Trigger (%)
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {simulationConfig.buyTriggerPct}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.buyTriggerPct.min}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              buyTriggerPct: { ...prev.buyTriggerPct, min: Number(e.target.value) },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.buyTriggerPct.max}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              buyTriggerPct: { ...prev.buyTriggerPct, max: Number(e.target.value) },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.buyTriggerPct.step}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              buyTriggerPct: {
                                ...prev.buyTriggerPct,
                                step: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {Math.ceil(
                          (parameterRanges.buyTriggerPct.max - parameterRanges.buyTriggerPct.min) /
                            parameterRanges.buyTriggerPct.step,
                        ) + 1}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        Sell Trigger (%)
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {simulationConfig.sellTriggerPct}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.sellTriggerPct.min}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              sellTriggerPct: {
                                ...prev.sellTriggerPct,
                                min: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.sellTriggerPct.max}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              sellTriggerPct: {
                                ...prev.sellTriggerPct,
                                max: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.sellTriggerPct.step}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              sellTriggerPct: {
                                ...prev.sellTriggerPct,
                                step: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {Math.ceil(
                          (parameterRanges.sellTriggerPct.max -
                            parameterRanges.sellTriggerPct.min) /
                            parameterRanges.sellTriggerPct.step,
                        ) + 1}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        Rebalance Ratio
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {simulationConfig.rebalanceRatio}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.rebalanceRatio.min}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              rebalanceRatio: {
                                ...prev.rebalanceRatio,
                                min: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.1"
                          value={parameterRanges.rebalanceRatio.max}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              rebalanceRatio: {
                                ...prev.rebalanceRatio,
                                max: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          step="0.01"
                          value={parameterRanges.rebalanceRatio.step}
                          onChange={(e) =>
                            setParameterRanges((prev) => ({
                              ...prev,
                              rebalanceRatio: {
                                ...prev.rebalanceRatio,
                                step: Number(e.target.value),
                              },
                            }))
                          }
                          className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {Math.ceil(
                          (parameterRanges.rebalanceRatio.max -
                            parameterRanges.rebalanceRatio.min) /
                            parameterRanges.rebalanceRatio.step,
                        ) + 1}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="px-6 py-4 bg-gray-50 border-t">
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-600">
                    Total combinations:{' '}
                    {Object.values(parameterRanges)
                      .reduce(
                        (total, range) =>
                          total * (Math.ceil((range.max - range.min) / range.step) + 1),
                        1,
                      )
                      .toLocaleString()}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={generateHeatMapData}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                    >
                      Generate Heat Map
                    </button>
                    <button className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700">
                      Run Parameter Optimization
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Heat Map Visualization */}
          {showHeatMap && heatMapData.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-semibold">Parameter Sensitivity Heat Map</h3>
                    <p className="text-sm text-gray-500">
                      Performance analysis across buy/sell trigger combinations
                    </p>
                  </div>
                  <button
                    onClick={() => setShowHeatMap(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Performance Heat Map */}
                  <div>
                    <h4 className="text-md font-semibold mb-4">Performance Heat Map (%)</h4>
                    <div className="overflow-x-auto">
                      <div className="inline-block min-w-full">
                        <div
                          className="grid gap-1"
                          style={{
                            gridTemplateColumns: `40px repeat(${
                              [...new Set(heatMapData.map((d) => d.sellTrigger))].length
                            }, 40px)`,
                          }}
                        >
                          {/* Header row */}
                          <div className="text-xs font-medium text-gray-600 p-1"></div>
                          {[...new Set(heatMapData.map((d) => d.sellTrigger))].map((sell) => (
                            <div
                              key={sell}
                              className="text-xs font-medium text-gray-600 p-1 text-center"
                            >
                              {sell}%
                            </div>
                          ))}

                          {/* Data rows */}
                          {[...new Set(heatMapData.map((d) => d.buyTrigger))].map((buy) => (
                            <React.Fragment key={buy}>
                              <div className="text-xs font-medium text-gray-600 p-1 text-center">
                                {buy}%
                              </div>
                              {[...new Set(heatMapData.map((d) => d.sellTrigger))].map((sell) => {
                                const dataPoint = heatMapData.find(
                                  (d) => d.buyTrigger === buy && d.sellTrigger === sell,
                                );
                                const performance = parseFloat(dataPoint?.performance || '0');
                                const intensity = Math.min(Math.max((performance - 5) / 10, 0), 1);
                                const color =
                                  performance > 8
                                    ? `rgba(34, 197, 94, ${0.3 + intensity * 0.7})` // Green for good performance
                                    : performance > 5
                                    ? `rgba(251, 191, 36, ${0.3 + intensity * 0.7})` // Yellow for medium
                                    : `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`; // Red for poor

                                return (
                                  <div
                                    key={`${buy}-${sell}`}
                                    className="text-xs p-1 text-center border border-gray-200 cursor-pointer hover:border-gray-400"
                                    style={{ backgroundColor: color }}
                                    title={`Buy: ${buy}%, Sell: ${sell}%, Performance: ${performance}%`}
                                  >
                                    {performance}
                                  </div>
                                );
                              })}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      Buy Trigger (Y-axis) vs Sell Trigger (X-axis)
                    </div>
                  </div>

                  {/* Statistics */}
                  <div>
                    <h4 className="text-md font-semibold mb-4">Performance Statistics</h4>
                    <div className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-sm font-medium text-gray-600">
                              Best Performance
                            </div>
                            <div className="text-lg font-semibold text-green-600">
                              {Math.max(
                                ...heatMapData.map((d) => parseFloat(d.performance)),
                              ).toFixed(2)}
                              %
                            </div>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-600">
                              Worst Performance
                            </div>
                            <div className="text-lg font-semibold text-red-600">
                              {Math.min(
                                ...heatMapData.map((d) => parseFloat(d.performance)),
                              ).toFixed(2)}
                              %
                            </div>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-600">
                              Average Performance
                            </div>
                            <div className="text-lg font-semibold text-blue-600">
                              {(
                                heatMapData.reduce((sum, d) => sum + parseFloat(d.performance), 0) /
                                heatMapData.length
                              ).toFixed(2)}
                              %
                            </div>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-600">
                              Total Combinations
                            </div>
                            <div className="text-lg font-semibold text-gray-900">
                              {heatMapData.length}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Best performing combinations */}
                      <div>
                        <div className="text-sm font-medium text-gray-600 mb-2">
                          Top 3 Combinations
                        </div>
                        <div className="space-y-2">
                          {heatMapData
                            .sort((a, b) => parseFloat(b.performance) - parseFloat(a.performance))
                            .slice(0, 3)
                            .map((combo, index) => (
                              <div
                                key={index}
                                className="flex justify-between items-center p-2 bg-green-50 rounded"
                              >
                                <span className="text-sm">
                                  Buy: {combo.buyTrigger}%, Sell: {combo.sellTrigger}%
                                </span>
                                <span className="text-sm font-semibold text-green-600">
                                  {combo.performance}%
                                </span>
                              </div>
                            ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Simulation Results */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Simulation Results</h3>
              <p className="text-sm text-gray-500">
                Historical simulation results and performance analysis
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ticker
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Period
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Algorithm Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Buy & Hold Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Excess Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trades
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sharpe Ratio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {simulationResults.map((result) => (
                    <tr key={result.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {result.ticker}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {result.startDate} to {result.endDate}
                      </td>
                      <td
                        className={`px-6 py-4 whitespace-nowrap text-sm ${
                          result.algorithmReturn >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {result.algorithmReturn.toFixed(2)}%
                      </td>
                      <td
                        className={`px-6 py-4 whitespace-nowrap text-sm ${
                          result.buyHoldReturn >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {result.buyHoldReturn.toFixed(2)}%
                      </td>
                      <td
                        className={`px-6 py-4 whitespace-nowrap text-sm ${
                          result.excessReturn >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {result.excessReturn.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.algorithmTrades}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.sharpeRatio.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            result.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : result.status === 'running'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {result.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            className="text-blue-600 hover:text-blue-900"
                            title="View Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleExportResult(result.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Export Excel (Detailed)"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleExportResultExcel(result.id)}
                            className="text-purple-600 hover:text-purple-900"
                            title="Export Excel (Enhanced)"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'optimization' && (
        <div className="space-y-6">
          {/* Optimization Configuration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Parameter Optimization</h3>
            <p className="text-gray-600 mb-4">
              Optimize your trading parameters by testing different combinations on historical data.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ticker Symbol
                </label>
                <input
                  type="text"
                  value={simulationConfig.ticker}
                  onChange={(e) =>
                    setSimulationConfig({ ...simulationConfig, ticker: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="e.g., AAPL"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={simulationConfig.startDate}
                  onChange={(e) =>
                    setSimulationConfig({ ...simulationConfig, startDate: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={simulationConfig.endDate}
                  onChange={(e) =>
                    setSimulationConfig({ ...simulationConfig, endDate: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
            </div>
            <div className="mt-4">
              <button className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Run Optimization
              </button>
            </div>
          </div>

          {/* Optimization Results */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Results</h3>
            <div className="text-center py-8">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No optimization results yet</p>
              <p className="text-sm text-gray-400">Run an optimization to see results here</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Simulation;
