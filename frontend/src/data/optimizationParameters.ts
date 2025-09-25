// Predefined optimization parameters with user-friendly names and descriptions
// This makes it easier for users to select parameters without knowing the exact variable names

export interface OptimizationParameter {
  id: string;
  name: string;
  description: string;
  parameter_type: 'float' | 'integer' | 'boolean' | 'categorical';
  default_min: number;
  default_max: number;
  default_step: number;
  unit: string;
  category: 'trading' | 'risk' | 'execution' | 'market';
  examples?: string[];
}

export const OPTIMIZATION_PARAMETERS: OptimizationParameter[] = [
  // Trading Parameters
  {
    id: 'trigger_threshold_pct',
    name: 'Trigger Threshold',
    description: 'Price movement percentage that triggers a rebalancing trade',
    parameter_type: 'float',
    default_min: 0.5,
    default_max: 5.0,
    default_step: 0.25,
    unit: '%',
    category: 'trading',
    examples: ['1.0% - Conservative', '2.0% - Moderate', '3.0% - Aggressive'],
  },
  {
    id: 'rebalance_ratio',
    name: 'Rebalance Ratio',
    description: 'Multiplier for calculating trade size when trigger is hit',
    parameter_type: 'float',
    default_min: 1.0,
    default_max: 3.0,
    default_step: 0.1,
    unit: 'x',
    category: 'trading',
    examples: ['1.5x - Conservative', '1.67x - Standard', '2.0x - Aggressive'],
  },
  {
    id: 'commission_rate',
    name: 'Commission Rate',
    description: 'Trading commission as percentage of trade value',
    parameter_type: 'float',
    default_min: 0.0,
    default_max: 0.01,
    default_step: 0.0001,
    unit: '%',
    category: 'execution',
    examples: ['0.0% - No commission', '0.01% - Low cost', '0.05% - Standard'],
  },

  // Risk Management Parameters
  {
    id: 'min_stock_alloc_pct',
    name: 'Minimum Stock Allocation',
    description: 'Minimum percentage of portfolio that must be in stock',
    parameter_type: 'float',
    default_min: 0.0,
    default_max: 0.5,
    default_step: 0.05,
    unit: '%',
    category: 'risk',
    examples: ['0% - No minimum', '25% - Conservative', '50% - Balanced'],
  },
  {
    id: 'max_stock_alloc_pct',
    name: 'Maximum Stock Allocation',
    description: 'Maximum percentage of portfolio that can be in stock',
    parameter_type: 'float',
    default_min: 0.5,
    default_max: 1.0,
    default_step: 0.05,
    unit: '%',
    category: 'risk',
    examples: ['75% - Conservative', '90% - Moderate', '100% - No limit'],
  },
  {
    id: 'max_orders_per_day',
    name: 'Maximum Orders Per Day',
    description: 'Limit on number of trades per day to control activity',
    parameter_type: 'integer',
    default_min: 1,
    default_max: 20,
    default_step: 1,
    unit: 'orders',
    category: 'risk',
    examples: ['1 - Very conservative', '5 - Moderate', '10 - Active'],
  },

  // Market Parameters
  {
    id: 'allow_after_hours',
    name: 'Allow After-Hours Trading',
    description: 'Whether to allow trading outside regular market hours',
    parameter_type: 'boolean',
    default_min: 0,
    default_max: 1,
    default_step: 1,
    unit: '',
    category: 'market',
    examples: ['No - Market hours only', 'Yes - Extended hours'],
  },

  // Execution Parameters
  {
    id: 'min_qty',
    name: 'Minimum Order Quantity',
    description: 'Minimum number of shares per trade',
    parameter_type: 'float',
    default_min: 0,
    default_max: 100,
    default_step: 1,
    unit: 'shares',
    category: 'execution',
    examples: ['0 - No minimum', '1 - Whole shares', '10 - Round lots'],
  },
  {
    id: 'min_notional',
    name: 'Minimum Order Value',
    description: 'Minimum dollar value per trade',
    parameter_type: 'float',
    default_min: 0,
    default_max: 1000,
    default_step: 50,
    unit: '$',
    category: 'execution',
    examples: ['$0 - No minimum', '$100 - Standard', '$500 - Large trades only'],
  },
];

export const getParameterById = (id: string): OptimizationParameter | undefined => {
  return OPTIMIZATION_PARAMETERS.find((param) => param.id === id);
};

export const getParametersByCategory = (category: string): OptimizationParameter[] => {
  return OPTIMIZATION_PARAMETERS.filter((param) => param.category === category);
};

export const getParameterCategories = (): string[] => {
  return [...new Set(OPTIMIZATION_PARAMETERS.map((param) => param.category))];
};
