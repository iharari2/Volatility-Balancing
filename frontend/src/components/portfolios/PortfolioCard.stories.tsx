import type { Meta, StoryObj } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';
import PortfolioCard, { Portfolio, PortfolioPosition } from './PortfolioCard';

const meta: Meta<typeof PortfolioCard> = {
  title: 'Portfolios/PortfolioCard',
  component: PortfolioCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div style={{ width: '380px' }}>
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

const basePortfolio: Portfolio = {
  id: 'portfolio-1',
  name: 'Growth Portfolio',
  description: 'High-growth tech stocks with volatility trading',
  totalValue: 125430.50,
  autoTradingEnabled: true,
  positionCount: 5,
};

const mockPositions: PortfolioPosition[] = [
  { id: 'pos-1', asset: 'AAPL', qty: 100 },
  { id: 'pos-2', asset: 'GOOGL', qty: 50 },
  { id: 'pos-3', asset: 'MSFT', qty: 75 },
  { id: 'pos-4', asset: 'NVDA', qty: 30 },
  { id: 'pos-5', asset: 'AMZN', qty: 40 },
];

export const Default: Story = {
  args: {
    portfolio: basePortfolio,
    onSelect: (id) => console.log('Selected:', id),
    onEdit: (id) => console.log('Edit:', id),
    onDelete: (id) => console.log('Delete:', id),
    onToggleExpand: (id) => console.log('Toggle:', id),
  },
};

export const Selected: Story = {
  args: {
    portfolio: basePortfolio,
    isSelected: true,
    onSelect: (id) => console.log('Selected:', id),
    onEdit: (id) => console.log('Edit:', id),
    onDelete: (id) => console.log('Delete:', id),
  },
};

export const ManualMode: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      autoTradingEnabled: false,
    },
  },
};

export const WithPnLPositive: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      pnl: 1234.56,
      pnlPct: 0.98,
    },
  },
};

export const WithPnLNegative: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      pnl: -567.89,
      pnlPct: -0.45,
    },
  },
};

export const Expanded: Story = {
  args: {
    portfolio: basePortfolio,
    positions: mockPositions,
    isExpanded: true,
    onToggleExpand: (id) => console.log('Toggle:', id),
  },
};

export const ExpandedLoading: Story = {
  args: {
    portfolio: basePortfolio,
    isExpanded: true,
    isLoadingPositions: true,
    onToggleExpand: (id) => console.log('Toggle:', id),
  },
};

export const ExpandedEmpty: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      positionCount: 0,
    },
    positions: [],
    isExpanded: true,
    onToggleExpand: (id) => console.log('Toggle:', id),
  },
};

export const NoDescription: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      description: undefined,
    },
  },
};

export const NoActions: Story = {
  args: {
    portfolio: basePortfolio,
    showActions: false,
  },
};

export const SmallValue: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      name: 'Starter Portfolio',
      description: 'Learning the ropes',
      totalValue: 1250.00,
      positionCount: 1,
    },
  },
};

export const LargeValue: Story = {
  args: {
    portfolio: {
      ...basePortfolio,
      name: 'Main Investment Account',
      description: 'Primary long-term holdings',
      totalValue: 1543267.89,
      positionCount: 12,
      pnl: 15432.10,
      pnlPct: 1.01,
    },
  },
};

// Grid view with multiple cards
export const GridView: Story = {
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div className="grid grid-cols-3 gap-4" style={{ width: '1200px' }}>
          <PortfolioCard
            portfolio={{
              id: '1',
              name: 'Growth Portfolio',
              description: 'High-growth tech stocks',
              totalValue: 125430.50,
              autoTradingEnabled: true,
              positionCount: 5,
              pnl: 1234.56,
              pnlPct: 0.98,
            }}
            isSelected={true}
          />
          <PortfolioCard
            portfolio={{
              id: '2',
              name: 'Income Portfolio',
              description: 'Dividend-focused investments',
              totalValue: 89750.25,
              autoTradingEnabled: false,
              positionCount: 8,
              pnl: -234.12,
              pnlPct: -0.26,
            }}
          />
          <PortfolioCard
            portfolio={{
              id: '3',
              name: 'Speculative',
              description: 'High-risk plays',
              totalValue: 15000.00,
              autoTradingEnabled: true,
              positionCount: 2,
            }}
          />
        </div>
      </MemoryRouter>
    ),
  ],
  render: () => <></>,
};
