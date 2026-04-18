import { X } from 'lucide-react';

interface MetricDef {
  name: string;
  formula: string;
  notes?: string;
}

interface Section {
  title: string;
  metrics: MetricDef[];
}

const SECTIONS: Section[] = [
  {
    title: 'Portfolio Analytics',
    metrics: [
      {
        name: 'Return',
        formula: '(Last Value − First Value) / First Value × 100',
        notes: 'Total percentage change in portfolio value over the selected period.',
      },
      {
        name: 'Volatility',
        formula: 'StdDev(daily returns) × √252 × 100',
        notes: 'Annualized standard deviation of daily portfolio returns, expressed as a percentage. Assumes 252 trading days per year.',
      },
      {
        name: 'Max Drawdown',
        formula: 'max((Peak − Value) / Peak) × 100',
        notes: 'Largest peak-to-trough decline observed in the portfolio value. A higher magnitude means a worse worst-case loss.',
      },
      {
        name: 'Sharpe-like Ratio',
        formula: 'Annualized Return / Annualized Volatility',
        notes: 'A simplified return-to-risk ratio. Unlike the standard Sharpe ratio, no risk-free rate is subtracted. Higher is better. Use this to compare strategies against each other, not against published Sharpe benchmarks.',
      },
      {
        name: 'Commission Total',
        formula: 'Σ commissions paid across all trades',
        notes: 'Cumulative brokerage fees paid over the selected period.',
      },
      {
        name: 'Dividend Total',
        formula: 'Σ net dividends received',
        notes: 'Total dividend income after withholding tax, across all positions in the period.',
      },
    ],
  },
  {
    title: 'Simulation Results',
    metrics: [
      {
        name: 'Final Value',
        formula: 'Stock holdings × Last Price + Cash',
        notes: 'Total portfolio value (market value of shares + remaining cash) at the end of the simulation.',
      },
      {
        name: 'Return',
        formula: '(Final Value − Initial Capital) / Initial Capital × 100',
        notes: 'Total percentage gain or loss relative to the starting capital.',
      },
      {
        name: 'Max Drawdown',
        formula: 'max((Peak − Value) / Peak) × 100',
        notes: 'Largest peak-to-trough decline in portfolio value during the simulation.',
      },
      {
        name: 'Volatility',
        formula: 'StdDev(daily returns) × √252',
        notes: 'Annualized standard deviation of daily portfolio returns. Computed from the simulation timeline.',
      },
      {
        name: 'Sharpe Ratio',
        formula: '(Mean Daily Return × 252) / (StdDev Daily Return × √252)',
        notes: 'Annualized Sharpe ratio without a risk-free rate deduction. Equivalent to Sharpe-like in analytics. A value above 1.0 is generally considered good.',
      },
      {
        name: 'Trades',
        formula: 'Count of executed buy + sell orders',
        notes: 'Total number of orders the algorithm triggered and executed. Each rebalance event counts as one trade.',
      },
      {
        name: 'Dividends',
        formula: 'Σ (DPS × Shares Held on ex-date) × (1 − Withholding Rate)',
        notes: 'Net dividend income credited to cash during the simulation. DPS = dividend per share.',
      },
      {
        name: 'Buy & Hold Return',
        formula: '(End Price − Start Price) / Start Price × 100',
        notes: 'Passive baseline: what you would have earned by buying the asset at the start and holding it unchanged until the end, with the same initial capital.',
      },
      {
        name: 'Alpha',
        formula: 'Strategy Return − Buy & Hold Return',
        notes: 'Excess return the algorithm generated versus passive holding. Positive alpha means the algorithm outperformed.',
      },
    ],
  },
];

interface MetricsMethodologyModalProps {
  onClose: () => void;
}

export default function MetricsMethodologyModal({ onClose }: MetricsMethodologyModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-900">How Metrics Are Calculated</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto px-6 py-4 space-y-6">
          {SECTIONS.map((section) => (
            <div key={section.title}>
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">
                {section.title}
              </h3>
              <div className="space-y-3">
                {section.metrics.map((m) => (
                  <div key={m.name} className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-3">
                    <div className="flex items-start gap-3">
                      <span className="min-w-[140px] text-sm font-semibold text-gray-800">{m.name}</span>
                      <div className="flex-1">
                        <code className="block text-xs font-mono text-primary-700 bg-primary-50 rounded px-2 py-1 mb-1.5">
                          {m.formula}
                        </code>
                        {m.notes && (
                          <p className="text-xs text-gray-500 leading-relaxed">{m.notes}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-100 text-xs text-gray-400">
          All calculations assume 252 trading days per year unless stated otherwise.
        </div>
      </div>
    </div>
  );
}
