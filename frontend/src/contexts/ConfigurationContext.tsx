import React, { createContext, useContext, useState, useEffect } from 'react';

export interface SharedConfiguration {
  triggerThresholdPct: number;
  rebalanceRatio: number;
  commissionRate: number;
  minNotional: number;
  allowAfterHours: boolean;
  guardrails: {
    minStockAllocPct: number;
    maxStockAllocPct: number;
    maxOrdersPerDay: number;
  };
  withholdingTaxRate: number;
}

const defaultConfiguration: SharedConfiguration = {
  triggerThresholdPct: 0.03, // 3%
  rebalanceRatio: 0.5,
  commissionRate: 0.0001, // 0.01%
  minNotional: 100,
  allowAfterHours: true,
  guardrails: {
    minStockAllocPct: 0.25, // 25%
    maxStockAllocPct: 0.75, // 75%
    maxOrdersPerDay: 5,
  },
  withholdingTaxRate: 0.25, // 25%
};

interface ConfigurationContextType {
  configuration: SharedConfiguration;
  updateConfiguration: (updates: Partial<SharedConfiguration>) => void;
  resetConfiguration: () => void;
}

const ConfigurationContext = createContext<ConfigurationContextType | undefined>(undefined);

export function ConfigurationProvider({ children }: { children: React.ReactNode }) {
  const [configuration, setConfiguration] = useState<SharedConfiguration>(() => {
    // Load from localStorage on initialization
    const saved = localStorage.getItem('volatility-balancing-config');
    if (saved) {
      try {
        return { ...defaultConfiguration, ...JSON.parse(saved) };
      } catch (error) {
        console.warn('Failed to parse saved configuration:', error);
      }
    }
    return defaultConfiguration;
  });

  // Save to localStorage whenever configuration changes
  useEffect(() => {
    localStorage.setItem('volatility-balancing-config', JSON.stringify(configuration));
  }, [configuration]);

  const updateConfiguration = (updates: Partial<SharedConfiguration>) => {
    setConfiguration((prev) => ({ ...prev, ...updates }));
  };

  const resetConfiguration = () => {
    setConfiguration(defaultConfiguration);
  };

  return (
    <ConfigurationContext.Provider
      value={{ configuration, updateConfiguration, resetConfiguration }}
    >
      {children}
    </ConfigurationContext.Provider>
  );
}

export function useConfiguration() {
  const context = useContext(ConfigurationContext);
  if (context === undefined) {
    throw new Error('useConfiguration must be used within a ConfigurationProvider');
  }
  return context;
}
