// Parameter Optimization System Types
// Frontend TypeScript definitions for the optimization system

export interface OptimizationConfig {
  id: string;
  name: string;
  ticker: string;
  start_date: string;
  end_date: string;
  parameter_ranges: Record<string, ParameterRange>;
  optimization_criteria: OptimizationCriteria;
  constraints: Constraint[];
  status: OptimizationStatus;
  total_combinations: number;
  created_at: string;
  updated_at: string;
}

export interface ParameterRange {
  parameter_type: ParameterType;
  min_value: number;
  max_value: number;
  step_size: number;
  description?: string;
}

export enum ParameterType {
  FLOAT = 'float',
  INTEGER = 'integer',
  BOOLEAN = 'boolean',
  CATEGORICAL = 'categorical',
}

export interface OptimizationCriteria {
  primary_metric: OptimizationMetric;
  secondary_metrics: OptimizationMetric[];
  minimize: boolean;
}

export interface Constraint {
  metric: OptimizationMetric;
  constraint_type: ConstraintType;
  value: number;
  description?: string;
}

export enum ConstraintType {
  MAX_VALUE = 'max_value',
  MIN_VALUE = 'min_value',
  EQUAL_TO = 'equal_to',
}

export enum OptimizationMetric {
  TOTAL_RETURN = 'total_return',
  SHARPE_RATIO = 'sharpe_ratio',
  MAX_DRAWDOWN = 'max_drawdown',
  VOLATILITY = 'volatility',
  CALMAR_RATIO = 'calmar_ratio',
  SORTINO_RATIO = 'sortino_ratio',
  WIN_RATE = 'win_rate',
  PROFIT_FACTOR = 'profit_factor',
  TRADE_COUNT = 'trade_count',
  AVG_TRADE_DURATION = 'avg_trade_duration',
}

export enum OptimizationStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface OptimizationResult {
  id: string;
  config_id: string;
  parameter_combination: ParameterCombination;
  metrics: Record<OptimizationMetric, number>;
  status: OptimizationResultStatus;
  created_at: string;
  completed_at?: string;
  // Additional properties for display
  parameters?: Record<string, any>;
  return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  volatility?: number;
  total_trades?: number;
  config?: Record<string, any>;
}

export interface ParameterCombination {
  combination_id: string;
  parameters: Record<string, any>;
}

export enum OptimizationResultStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface OptimizationProgress {
  config_id: string;
  status: OptimizationStatus;
  progress_percentage: number;
  completed_combinations: number;
  total_combinations: number;
  estimated_completion_time?: string;
  current_combination?: ParameterCombination;
}

export interface HeatmapData {
  x_parameter: string;
  y_parameter: string;
  metric: OptimizationMetric;
  cells: HeatmapCell[];
  statistics: HeatmapStatistics;
  // Optional arrays of unique values for axes (can be derived from cells if not provided)
  x_values?: number[];
  y_values?: number[];
}

export interface HeatmapCell {
  x_value: number;
  y_value: number;
  metric_value: number;
  parameter_combination: ParameterCombination;
  is_valid?: boolean; // Optional validity flag, defaults to true if cell exists
}

export interface HeatmapStatistics {
  min: number;
  max: number;
  mean: number;
  median: number;
  std_dev: number;
}

// API Request/Response Types
export interface CreateConfigRequest {
  name: string;
  ticker: string;
  start_date: string;
  end_date: string;
  parameter_ranges: Record<string, ParameterRangeRequest>;
  optimization_criteria: OptimizationCriteriaRequest;
  constraints: ConstraintRequest[];
  initial_cash?: number;
  intraday_interval_minutes?: number;
  include_after_hours?: boolean;
}

export interface ParameterRangeRequest {
  parameter_type: ParameterType;
  min_value: number;
  max_value: number;
  step_size: number;
  description?: string;
}

export interface OptimizationCriteriaRequest {
  primary_metric: OptimizationMetric;
  secondary_metrics: OptimizationMetric[];
  minimize: boolean;
}

export interface ConstraintRequest {
  metric: OptimizationMetric;
  constraint_type: ConstraintType;
  value: number;
  description?: string;
}

export interface ConfigResponse {
  id: string;
  name: string;
  ticker: string;
  start_date: string;
  end_date: string;
  parameter_ranges: Record<string, ParameterRange>;
  optimization_criteria: OptimizationCriteria;
  constraints: Constraint[];
  status: OptimizationStatus;
  total_combinations: number;
  created_at: string;
  updated_at: string;
  initial_cash: number;
  intraday_interval_minutes: number;
  include_after_hours: boolean;
}

export interface StartResponse {
  message: string;
  config_id: string;
  status: OptimizationStatus;
}

export interface ProgressResponse {
  config_id: string;
  status: OptimizationStatus;
  progress_percentage: number;
  completed_combinations: number;
  total_combinations: number;
  estimated_completion_time?: string;
  current_combination?: ParameterCombination;
}

export interface ResultsResponse {
  config_id: string;
  results: OptimizationResult[];
  total_count: number;
}

export interface HeatmapRequest {
  x_parameter: string;
  y_parameter: string;
  metric: OptimizationMetric;
}

export interface MetricInfo {
  value: string;
  name: string;
  description: string;
}

export interface MetricsResponse {
  metrics: MetricInfo[];
}

export interface ParameterTypeInfo {
  value: string;
  name: string;
  description: string;
}

export interface ParameterTypesResponse {
  parameter_types: ParameterTypeInfo[];
}

// UI State Types
export interface OptimizationState {
  configs: OptimizationConfig[];
  activeOptimizations: Map<string, OptimizationProgress>;
  results: Map<string, OptimizationResult[]>;
  heatmapData: Map<string, HeatmapData>;
  loading: boolean;
  error: string | null;
}

export interface OptimizationContextType {
  state: OptimizationState;
  createConfig: (config: CreateConfigRequest) => Promise<void>;
  getConfig: (id: string) => Promise<OptimizationConfig | null>;
  startOptimization: (id: string) => Promise<void>;
  getProgress: (id: string) => Promise<OptimizationProgress | null>;
  getResults: (id: string) => Promise<OptimizationResult[]>;
  getHeatmap: (
    id: string,
    x: string,
    y: string,
    metric: OptimizationMetric,
  ) => Promise<HeatmapData | null>;
  getMetrics: () => Promise<OptimizationMetric[]>;
  getParameterTypes: () => Promise<ParameterTypeInfo[]>;
  refreshProgress: (id: string) => Promise<void>;
  clearError: () => void;
}
