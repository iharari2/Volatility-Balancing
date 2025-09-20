import { useState } from 'react';
import { OrderPolicy, Guardrails } from '../types';
import { Settings, Save, RotateCcw } from 'lucide-react';
import UnifiedConfigPanel, { UnifiedConfig } from './UnifiedConfigPanel';

interface PositionConfigPanelProps {
  orderPolicy: OrderPolicy;
  guardrails: Guardrails;
  withholdingTaxRate: number;
  onSave: (config: {
    orderPolicy: OrderPolicy;
    guardrails: Guardrails;
    withholdingTaxRate: number;
  }) => void;
  onReset: () => void;
  isLoading?: boolean;
}

const defaultOrderPolicy: OrderPolicy = {
  min_qty: 0,
  min_notional: 100,
  lot_size: 0,
  qty_step: 0,
  action_below_min: 'hold',
  trigger_threshold_pct: 0.03, // 3%
  rebalance_ratio: 0.5, // Updated to match simulation default
  commission_rate: 0.0001, // 0.01%
  allow_after_hours: true, // Default to after hours ON
};

const defaultGuardrails: Guardrails = {
  min_stock_alloc_pct: 0.25, // 25%
  max_stock_alloc_pct: 0.75, // 75%
  max_orders_per_day: 5,
};

// Convert between OrderPolicy/Guardrails and UnifiedConfig
const convertToUnifiedConfig = (
  orderPolicy: OrderPolicy,
  guardrails: Guardrails,
): UnifiedConfig => ({
  ticker: 'AAPL', // Default ticker for position config
  initialCash: 10000, // Default cash for position config
  triggerThresholdPct: orderPolicy.trigger_threshold_pct,
  rebalanceRatio: orderPolicy.rebalance_ratio,
  commissionRate: orderPolicy.commission_rate,
  minNotional: orderPolicy.min_notional,
  allowAfterHours: orderPolicy.allow_after_hours,
  guardrails: {
    minStockAllocPct: guardrails.min_stock_alloc_pct,
    maxStockAllocPct: guardrails.max_stock_alloc_pct,
    maxOrdersPerDay: guardrails.max_orders_per_day,
  },
});

const convertFromUnifiedConfig = (
  config: UnifiedConfig,
): { orderPolicy: OrderPolicy; guardrails: Guardrails } => ({
  orderPolicy: {
    min_qty: 0,
    min_notional: config.minNotional,
    lot_size: 0,
    qty_step: 0,
    action_below_min: 'hold',
    trigger_threshold_pct: config.triggerThresholdPct,
    rebalance_ratio: config.rebalanceRatio,
    commission_rate: config.commissionRate,
    allow_after_hours: config.allowAfterHours,
  },
  guardrails: {
    min_stock_alloc_pct: config.guardrails.minStockAllocPct,
    max_stock_alloc_pct: config.guardrails.maxStockAllocPct,
    max_orders_per_day: config.guardrails.maxOrdersPerDay,
  },
});

export default function PositionConfigPanel({
  orderPolicy,
  guardrails,
  withholdingTaxRate,
  onSave,
  onReset,
  isLoading = false,
}: PositionConfigPanelProps) {
  const [config, setConfig] = useState({
    orderPolicy: { ...orderPolicy },
    guardrails: { ...guardrails },
    withholdingTaxRate,
  });

  // Convert to unified config for the panel
  const unifiedConfig = convertToUnifiedConfig(config.orderPolicy, config.guardrails);

  const handleUnifiedConfigChange = (unifiedConfig: UnifiedConfig) => {
    const converted = convertFromUnifiedConfig(unifiedConfig);
    setConfig({
      orderPolicy: converted.orderPolicy,
      guardrails: converted.guardrails,
      withholdingTaxRate: config.withholdingTaxRate,
    });
  };

  const handleSave = () => {
    onSave(config);
  };

  const handleReset = () => {
    setConfig({
      orderPolicy: { ...defaultOrderPolicy },
      guardrails: { ...defaultGuardrails },
      withholdingTaxRate: 0.25,
    });
    onReset();
  };

  return (
    <div className="space-y-6">
      {/* Unified Configuration Panel */}
      <UnifiedConfigPanel
        config={unifiedConfig}
        onConfigChange={handleUnifiedConfigChange}
        onSave={handleSave}
        onReset={handleReset}
        isLoading={isLoading}
        mode="trading"
        showAdvanced={true}
      />

      {/* Dividend Settings - Keep this as it's specific to trading */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Dividend Settings</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Withholding Tax Rate (%)</label>
            <input
              type="number"
              value={config.withholdingTaxRate * 100}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, withholdingTaxRate: Number(e.target.value) / 100 }))
              }
              className="input"
              min="0"
              max="50"
              step="0.1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tax withholding rate for dividends (default: 25%)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
