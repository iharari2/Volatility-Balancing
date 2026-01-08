import { useState, useMemo } from 'react';
import { X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { portfolioApi } from '../../lib/api';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface CreatePortfolioWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (portfolioId: string) => void;
}

interface PortfolioData {
  name: string;
  description: string;
  portfolioType: 'live' | 'simulation' | 'sandbox';
  strategyTemplate: 'default' | 'conservative' | 'aggressive' | 'custom';
  marketHoursPolicy: 'market-open-only' | 'allow-after-hours';
}

// Template configurations
const TEMPLATE_CONFIGS: Record<
  'default' | 'conservative' | 'aggressive' | 'custom',
  {
    triggerUp: number;
    triggerDown: number;
    minStockPct: number;
    maxStockPct: number;
    maxTradePctOfPosition: number;
    commission: number;
    description: string;
  }
> = {
  default: {
    triggerUp: 3.0,
    triggerDown: -3.0,
    minStockPct: 20,
    maxStockPct: 60,
    maxTradePctOfPosition: 10,
    commission: 0.1,
    description: 'Balanced trading frequency and risk limits.',
  },
  conservative: {
    triggerUp: 4.0,
    triggerDown: -4.0,
    minStockPct: 15,
    maxStockPct: 50,
    maxTradePctOfPosition: 5,
    commission: 0.1,
    description: 'Fewer trades, tighter exposure, smaller trade sizes.',
  },
  aggressive: {
    triggerUp: 2.0,
    triggerDown: -2.0,
    minStockPct: 25,
    maxStockPct: 75,
    maxTradePctOfPosition: 15,
    commission: 0.1,
    description: 'More trades, larger trade sizes, broader exposure allowed.',
  },
  custom: {
    triggerUp: 3.0,
    triggerDown: -3.0,
    minStockPct: 20,
    maxStockPct: 60,
    maxTradePctOfPosition: 10,
    commission: 0.1,
    description: 'Start from Default then edit parameters immediately after creation.',
  },
};

export default function CreatePortfolioWizard({
  isOpen,
  onClose,
  onComplete,
}: CreatePortfolioWizardProps) {
  const navigate = useNavigate();
  const { selectedTenantId, setSelectedPortfolioId, refreshPortfolios, portfolios } =
    useTenantPortfolio();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<PortfolioData>({
    name: '',
    description: '',
    portfolioType: 'live',
    strategyTemplate: 'default',
    marketHoursPolicy: 'market-open-only',
  });

  const currentTemplate = useMemo(() => {
    try {
      const template = TEMPLATE_CONFIGS[formData.strategyTemplate];
      // Fallback to default if template not found
      if (!template) {
        console.warn(`Template "${formData.strategyTemplate}" not found, using default`);
        return TEMPLATE_CONFIGS.default;
      }
      return template;
    } catch (error) {
      console.error('Error loading template config:', error);
      return TEMPLATE_CONFIGS.default;
    }
  }, [formData.strategyTemplate]);

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate required fields
      if (!formData.name.trim() || formData.name.length < 3) {
        setError('Portfolio name must be at least 3 characters');
        setLoading(false);
        return;
      }

      // Check for duplicate portfolio name
      const normalizedName = formData.name.trim().toLowerCase();
      const duplicate = portfolios.find((p) => p.name.trim().toLowerCase() === normalizedName);
      if (duplicate) {
        setError(
          `Portfolio with name "${formData.name}" already exists. Please choose a different name.`,
        );
        setLoading(false);
        return;
      }

      if (!selectedTenantId) {
        setError('No tenant selected. Please select a tenant first.');
        setLoading(false);
        return;
      }

      // Create portfolio via API with metadata only
      const result = await portfolioApi.create(selectedTenantId, {
        name: formData.name,
        description: formData.description || undefined,
        type: formData.portfolioType.toUpperCase(), // LIVE, SIMULATION, SANDBOX
        template: formData.strategyTemplate.toUpperCase(), // DEFAULT, CONSERVATIVE, AGGRESSIVE, CUSTOM
        hours_policy:
          formData.marketHoursPolicy === 'market-open-only' ? 'OPEN_ONLY' : 'OPEN_PLUS_AFTER_HOURS',
      });

      const portfolioId = result.portfolio_id;

      // Reset form
      setFormData({
        name: '',
        description: '',
        portfolioType: 'live',
        strategyTemplate: 'default',
        marketHoursPolicy: 'market-open-only',
      });
      setStep(1);
      onClose();

      // Refresh portfolios list and set the new portfolio as selected
      await refreshPortfolios();
      setSelectedPortfolioId(portfolioId);

      // Redirect to portfolio overview
      if (onComplete) {
        onComplete(portfolioId);
      } else {
        // Navigate to portfolio overview page
        navigate(`/portfolios/${portfolioId}`);
      }
    } catch (err: any) {
      // Handle validation errors from backend (e.g., duplicate name)
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to create portfolio';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.name.trim().length >= 3;
      case 2:
        // Optional step, always can proceed
        return true;
      case 3:
        return formData.name.trim().length >= 3;
      default:
        return false;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">Create Portfolio</h3>
                <p className="text-sm text-gray-500 mt-1">Step {step} of 3</p>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Form */}
              <div className="lg:col-span-2 space-y-6 overflow-x-auto">
                {/* Step 1: Basics */}
                {step === 1 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">Basics</h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Portfolio Name <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., Blue Chips – Semi Passive"
                          />
                          {formData.name.length > 0 && formData.name.length < 3 && (
                            <p className="text-xs text-red-600 mt-1">
                              Name must be at least 3 characters
                            </p>
                          )}
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Description
                          </label>
                          <textarea
                            value={formData.description}
                            onChange={(e) =>
                              setFormData({ ...formData, description: e.target.value })
                            }
                            rows={3}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Optional description"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Portfolio Type <span className="text-red-500">*</span>
                          </label>
                          <div className="space-y-2">
                            <label className="flex items-start">
                              <input
                                type="radio"
                                name="portfolioType"
                                value="live"
                                checked={formData.portfolioType === 'live'}
                                onChange={(e) =>
                                  setFormData({
                                    ...formData,
                                    portfolioType: e.target.value as PortfolioData['portfolioType'],
                                  })
                                }
                                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                              />
                              <div className="ml-3">
                                <span className="text-sm font-medium text-gray-700">Live</span>
                                <p className="text-xs text-gray-500">(connect to broker later)</p>
                              </div>
                            </label>
                            <label className="flex items-start">
                              <input
                                type="radio"
                                name="portfolioType"
                                value="simulation"
                                checked={formData.portfolioType === 'simulation'}
                                onChange={(e) =>
                                  setFormData({
                                    ...formData,
                                    portfolioType: e.target.value as PortfolioData['portfolioType'],
                                  })
                                }
                                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                              />
                              <div className="ml-3">
                                <span className="text-sm font-medium text-gray-700">
                                  Simulation
                                </span>
                                <p className="text-xs text-gray-500">(historical backtests)</p>
                              </div>
                            </label>
                            <label className="flex items-start">
                              <input
                                type="radio"
                                name="portfolioType"
                                value="sandbox"
                                checked={formData.portfolioType === 'sandbox'}
                                onChange={(e) =>
                                  setFormData({
                                    ...formData,
                                    portfolioType: e.target.value as PortfolioData['portfolioType'],
                                  })
                                }
                                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                              />
                              <div className="ml-3">
                                <span className="text-sm font-medium text-gray-700">Sandbox</span>
                                <p className="text-xs text-gray-500">(paper trading)</p>
                              </div>
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Strategy Configuration */}
                {step === 2 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">
                        Strategy Configuration
                      </h4>
                      {!currentTemplate && (
                        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-md p-3">
                          <p className="text-sm text-yellow-800">
                            Warning: Template configuration not found. Using default settings.
                          </p>
                        </div>
                      )}
                      <div className="space-y-3">
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="default"
                            checked={formData.strategyTemplate === 'default'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Default</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.default.description}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="conservative"
                            checked={formData.strategyTemplate === 'conservative'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Conservative</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.conservative.description}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="aggressive"
                            checked={formData.strategyTemplate === 'aggressive'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Aggressive</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.aggressive.description}
                            </p>
                          </div>
                        </label>
                        <label className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer">
                          <input
                            type="radio"
                            name="strategyTemplate"
                            value="custom"
                            checked={formData.strategyTemplate === 'custom'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                strategyTemplate: e.target
                                  .value as PortfolioData['strategyTemplate'],
                              })
                            }
                            className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <span className="text-sm font-medium text-gray-700">Custom</span>
                            <p className="text-xs text-gray-500 mt-1">
                              {TEMPLATE_CONFIGS.custom.description}
                            </p>
                          </div>
                        </label>
                      </div>

                      <div className="mt-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Market Hours Policy
                        </label>
                        <div className="space-y-2">
                          <label className="flex items-center">
                            <input
                              type="radio"
                              name="marketHoursPolicy"
                              value="market-open-only"
                              checked={formData.marketHoursPolicy === 'market-open-only'}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  marketHoursPolicy: e.target
                                    .value as PortfolioData['marketHoursPolicy'],
                                })
                              }
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <span className="ml-2 text-sm text-gray-700">Market open only</span>
                          </label>
                          <label className="flex items-center">
                            <input
                              type="radio"
                              name="marketHoursPolicy"
                              value="allow-after-hours"
                              checked={formData.marketHoursPolicy === 'allow-after-hours'}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  marketHoursPolicy: e.target
                                    .value as PortfolioData['marketHoursPolicy'],
                                })
                              }
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                            />
                            <span className="ml-2 text-sm text-gray-700">Allow after-hours</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Review */}
                {step === 3 && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 mb-4">Review & Create</h4>
                      <div className="space-y-3 text-sm text-gray-700">
                        <div className="border border-gray-200 rounded-md p-3">
                          <h5 className="text-sm font-semibold text-gray-900 mb-2">
                            Portfolio Metadata
                          </h5>
                          <div>Name: {formData.name || '—'}</div>
                          <div>
                            Type: {formData.portfolioType.charAt(0).toUpperCase()}
                            {formData.portfolioType.slice(1)}
                          </div>
                          <div>Description: {formData.description || '—'}</div>
                        </div>
                        <div className="border border-gray-200 rounded-md p-3">
                          <h5 className="text-sm font-semibold text-gray-900 mb-2">
                            Strategy Config
                          </h5>
                          <div>
                            Template:{' '}
                            {formData.strategyTemplate.charAt(0).toUpperCase()}
                            {formData.strategyTemplate.slice(1)}
                          </div>
                          <div>
                            Market Hours:{' '}
                            {formData.marketHoursPolicy === 'market-open-only'
                              ? 'Market open only'
                              : 'Allow after-hours'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column - Helper/Preview */}
              <div className="lg:col-span-1">
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  {step === 1 && (
                    <div className="space-y-3">
                      <h5 className="text-sm font-semibold text-gray-900">What is a Portfolio?</h5>
                      <ul className="text-xs text-gray-600 space-y-2">
                        <li>• A portfolio belongs to a Tenant and groups positions.</li>
                        <li>
                          • It also has a strategy configuration (triggers, guardrails,
                          commissions).
                        </li>
                      </ul>
                      <div className="mt-4">
                        <h6 className="text-xs font-semibold text-gray-900 mb-2">Type guide:</h6>
                        <ul className="text-xs text-gray-600 space-y-1">
                          <li>
                            <strong>Live:</strong> Use for real-time trading cycles (engine runs in
                            backend).
                          </li>
                          <li>
                            <strong>Simulation:</strong> Use for backtesting on historical data.
                          </li>
                          <li>
                            <strong>Sandbox:</strong> Like live, but no real broker execution.
                          </li>
                        </ul>
                      </div>
                    </div>
                  )}

                  {step === 2 && currentTemplate && (
                    <div className="space-y-3">
                      <h5 className="text-sm font-semibold text-gray-900">
                        Effective Config Preview
                      </h5>
                      <div className="space-y-3 text-xs">
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Trigger thresholds</h6>
                          <div className="space-y-1 text-gray-600">
                            <div>
                              Up: {currentTemplate.triggerUp > 0 ? '+' : ''}
                              {currentTemplate.triggerUp}%
                            </div>
                            <div>Down: {currentTemplate.triggerDown}%</div>
                          </div>
                        </div>
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Guardrails</h6>
                          <div className="space-y-1 text-gray-600">
                            <div>Min stock %: {currentTemplate.minStockPct}%</div>
                            <div>Max stock %: {currentTemplate.maxStockPct}%</div>
                            <div>
                              Max trade % of position: {currentTemplate.maxTradePctOfPosition}%
                            </div>
                          </div>
                        </div>
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Commission</h6>
                          <div className="text-gray-600">
                            Base rate: {currentTemplate.commission}%
                          </div>
                        </div>
                        <div>
                          <h6 className="font-semibold text-gray-700 mb-1">Market Hours Policy</h6>
                          <div className="text-gray-600">
                            {formData.marketHoursPolicy === 'market-open-only'
                              ? 'Market open only'
                              : 'Allow after-hours'}
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-3 pt-3 border-t">
                          Note: You can edit these later in Positions & Config.
                        </p>
                      </div>
                    </div>
                  )}

                  {step === 3 && (
                    <div className="space-y-3">
                      <h5 className="text-sm font-semibold text-gray-900">Ready to Create</h5>
                      <ul className="text-xs text-gray-600 space-y-2">
                        <li>• Portfolio metadata will be saved first.</li>
                        <li>• You can add positions after creation.</li>
                        <li>• You can edit positions and config anytime.</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="mt-6 flex items-center justify-between border-t pt-4">
              <div>
                {step > 1 && (
                  <button
                    onClick={handleBack}
                    disabled={loading}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    ← Back
                  </button>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={onClose}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                {step < 3 ? (
                  <button
                    onClick={handleNext}
                    disabled={!canProceed() || loading}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next →
                  </button>
                ) : (
                  <button
                    onClick={handleSubmit}
                    disabled={loading || !canProceed()}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Creating...' : 'Create Portfolio'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
