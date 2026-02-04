import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Check, AlertCircle } from 'lucide-react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

// Storage keys
const TENANT_DEFAULTS_KEY = 'vb_tenant_defaults';
const SYSTEM_SETTINGS_KEY = 'vb_system_settings';

// Default values for tenant defaults
const DEFAULT_TENANT_DEFAULTS = {
  triggerUpPct: 3.0,
  triggerDownPct: -3.0,
  minStockPct: 20,
  maxStockPct: 60,
  maxTradePct: 10,
  commissionPct: 0.1,
};

// Default values for system settings
const DEFAULT_SYSTEM_SETTINGS = {
  theme: 'light' as 'light' | 'dark',
  refreshInterval: 60,
};

export default function SettingsPage() {
  const { selectedTenant } = useTenantPortfolio();

  // Tenant defaults state
  const [triggerUpPct, setTriggerUpPct] = useState(DEFAULT_TENANT_DEFAULTS.triggerUpPct);
  const [triggerDownPct, setTriggerDownPct] = useState(DEFAULT_TENANT_DEFAULTS.triggerDownPct);
  const [minStockPct, setMinStockPct] = useState(DEFAULT_TENANT_DEFAULTS.minStockPct);
  const [maxStockPct, setMaxStockPct] = useState(DEFAULT_TENANT_DEFAULTS.maxStockPct);
  const [maxTradePct, setMaxTradePct] = useState(DEFAULT_TENANT_DEFAULTS.maxTradePct);
  const [commissionPct, setCommissionPct] = useState(DEFAULT_TENANT_DEFAULTS.commissionPct);

  // System settings state
  const [theme, setTheme] = useState<'light' | 'dark'>(DEFAULT_SYSTEM_SETTINGS.theme);
  const [refreshInterval, setRefreshInterval] = useState(DEFAULT_SYSTEM_SETTINGS.refreshInterval);

  // Feedback state
  const [tenantSaveStatus, setTenantSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [systemSaveStatus, setSystemSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Load saved settings on mount
  useEffect(() => {
    try {
      // Load tenant defaults
      const savedTenantDefaults = localStorage.getItem(TENANT_DEFAULTS_KEY);
      if (savedTenantDefaults) {
        const parsed = JSON.parse(savedTenantDefaults);
        setTriggerUpPct(parsed.triggerUpPct ?? DEFAULT_TENANT_DEFAULTS.triggerUpPct);
        setTriggerDownPct(parsed.triggerDownPct ?? DEFAULT_TENANT_DEFAULTS.triggerDownPct);
        setMinStockPct(parsed.minStockPct ?? DEFAULT_TENANT_DEFAULTS.minStockPct);
        setMaxStockPct(parsed.maxStockPct ?? DEFAULT_TENANT_DEFAULTS.maxStockPct);
        setMaxTradePct(parsed.maxTradePct ?? DEFAULT_TENANT_DEFAULTS.maxTradePct);
        setCommissionPct(parsed.commissionPct ?? DEFAULT_TENANT_DEFAULTS.commissionPct);
      }

      // Load system settings
      const savedSystemSettings = localStorage.getItem(SYSTEM_SETTINGS_KEY);
      if (savedSystemSettings) {
        const parsed = JSON.parse(savedSystemSettings);
        setTheme(parsed.theme ?? DEFAULT_SYSTEM_SETTINGS.theme);
        setRefreshInterval(parsed.refreshInterval ?? DEFAULT_SYSTEM_SETTINGS.refreshInterval);
      }
    } catch (error) {
      console.error('Error loading settings from localStorage:', error);
    }
  }, []);

  // Save tenant defaults
  const handleSaveTenantDefaults = () => {
    try {
      const tenantDefaults = {
        triggerUpPct,
        triggerDownPct,
        minStockPct,
        maxStockPct,
        maxTradePct,
        commissionPct,
      };
      localStorage.setItem(TENANT_DEFAULTS_KEY, JSON.stringify(tenantDefaults));
      setTenantSaveStatus('success');
      setTimeout(() => setTenantSaveStatus('idle'), 3000);
    } catch (error) {
      console.error('Error saving tenant defaults:', error);
      setTenantSaveStatus('error');
      setTimeout(() => setTenantSaveStatus('idle'), 3000);
    }
  };

  // Save system settings
  const handleSaveSystemSettings = () => {
    try {
      const systemSettings = {
        theme,
        refreshInterval,
      };
      localStorage.setItem(SYSTEM_SETTINGS_KEY, JSON.stringify(systemSettings));
      setSystemSaveStatus('success');
      setTimeout(() => setSystemSaveStatus('idle'), 3000);

      // Apply theme immediately (optional - you could implement dark mode here)
      document.documentElement.classList.toggle('dark', theme === 'dark');
    } catch (error) {
      console.error('Error saving system settings:', error);
      setSystemSaveStatus('error');
      setTimeout(() => setSystemSaveStatus('idle'), 3000);
    }
  };

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
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        </div>
      </div>

      {/* Tenant Defaults */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Tenant Defaults</h2>
        <p className="text-sm text-gray-500 mb-4">
          These defaults will be used when creating new portfolios. Changes only affect future portfolios.
        </p>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Trigger Config
            </label>
            <p className="text-sm text-gray-500">
              Configure default trigger thresholds for new portfolios
            </p>
            <div className="mt-2 grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Up Threshold %</label>
                <input
                  type="number"
                  step="0.1"
                  value={triggerUpPct}
                  onChange={(e) => setTriggerUpPct(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Down Threshold %</label>
                <input
                  type="number"
                  step="0.1"
                  value={triggerDownPct}
                  onChange={(e) => setTriggerDownPct(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Default Guardrails</label>
            <p className="text-sm text-gray-500">Set default allocation limits</p>
            <div className="mt-2 grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Min Stock %</label>
                <input
                  type="number"
                  value={minStockPct}
                  onChange={(e) => setMinStockPct(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Max Stock %</label>
                <input
                  type="number"
                  value={maxStockPct}
                  onChange={(e) => setMaxStockPct(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Max Trade Size %</label>
                <input
                  type="number"
                  value={maxTradePct}
                  onChange={(e) => setMaxTradePct(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Default Commission</label>
            <p className="text-sm text-gray-500">Default commission rate for new portfolios</p>
            <div className="mt-2 flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                value={commissionPct}
                onChange={(e) => setCommissionPct(parseFloat(e.target.value) || 0)}
                className="w-32 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-500">%</span>
            </div>
          </div>

          <div className="pt-4 flex items-center gap-3">
            <button
              onClick={handleSaveTenantDefaults}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Save Tenant Defaults
            </button>
            {tenantSaveStatus === 'success' && (
              <span className="inline-flex items-center gap-1 text-sm text-green-600">
                <Check className="h-4 w-4" />
                Saved successfully
              </span>
            )}
            {tenantSaveStatus === 'error' && (
              <span className="inline-flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                Failed to save
              </span>
            )}
          </div>
        </div>
      </div>

      {/* System Settings */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">System</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="theme"
                  value="light"
                  checked={theme === 'light'}
                  onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Light</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="theme"
                  value="dark"
                  checked={theme === 'dark'}
                  onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Dark</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Refresh Interval (seconds)
            </label>
            <input
              type="number"
              min="10"
              max="300"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="w-full max-w-xs rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              How often to refresh market data and portfolio values
            </p>
          </div>

          <div className="pt-4 flex items-center gap-3">
            <button
              onClick={handleSaveSystemSettings}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Save System Settings
            </button>
            {systemSaveStatus === 'success' && (
              <span className="inline-flex items-center gap-1 text-sm text-green-600">
                <Check className="h-4 w-4" />
                Saved successfully
              </span>
            )}
            {systemSaveStatus === 'error' && (
              <span className="inline-flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                Failed to save
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
