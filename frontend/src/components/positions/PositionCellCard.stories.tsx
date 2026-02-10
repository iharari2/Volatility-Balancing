import type { Meta, StoryObj } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';
import PositionCellCard from './PositionCellCard';

// Mock the API module
const mockMarketApi = {
  getPrice: async () => ({
    price: 185.50,
    open: 183.00,
    high: 186.75,
    low: 182.50,
    close: 184.25,
    is_market_hours: true,
  }),
};

// Mock the positions API
const mockGetPositionEvents = async () => [];

const meta: Meta<typeof PositionCellCard> = {
  title: 'Positions/PositionCellCard',
  component: PositionCellCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div style={{ maxWidth: '800px' }}>
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
  // Note: In a real setup, you'd mock the API calls properly with MSW or similar
};

export default meta;
type Story = StoryObj<typeof meta>;

const basePosition = {
  id: 'pos-123',
  asset: 'AAPL',
  qty: 100,
  cash: 5000,
  anchor_price: 180.00,
  avg_cost: 175.00,
  status: 'ACTIVE',
};

const baseConfig = {
  trigger_up_pct: 3,
  trigger_down_pct: -3,
  min_stock_pct: 30,
  max_stock_pct: 70,
};

export const Default: Story = {
  args: {
    position: basePosition,
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50,
    compact: false,
  },
};

export const Compact: Story = {
  args: {
    position: basePosition,
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50,
    compact: true,
  },
};

export const CompactGrid: Story = {
  render: () => (
    <MemoryRouter>
      <div className="grid grid-cols-3 gap-4">
        <PositionCellCard
          position={{ ...basePosition, asset: 'AAPL' }}
          portfolioId="portfolio-1"
          tenantId="tenant-1"
          config={baseConfig}
          initialPrice={185.50}
          compact
        />
        <PositionCellCard
          position={{ ...basePosition, id: 'pos-456', asset: 'GOOGL', qty: 50, cash: 10000, anchor_price: 140.00 }}
          portfolioId="portfolio-1"
          tenantId="tenant-1"
          config={baseConfig}
          initialPrice={142.25}
          compact
        />
        <PositionCellCard
          position={{ ...basePosition, id: 'pos-789', asset: 'MSFT', qty: 75, cash: 7500, anchor_price: 410.00, status: 'PAUSED' }}
          portfolioId="portfolio-1"
          tenantId="tenant-1"
          config={baseConfig}
          initialPrice={405.00}
          compact
        />
      </div>
    </MemoryRouter>
  ),
};

export const Paused: Story = {
  args: {
    position: {
      ...basePosition,
      status: 'PAUSED',
    },
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50,
    compact: false,
  },
};

export const PriceUp: Story = {
  args: {
    position: {
      ...basePosition,
      anchor_price: 170.00,
    },
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50, // Price is up from anchor
  },
};

export const PriceDown: Story = {
  args: {
    position: {
      ...basePosition,
      anchor_price: 200.00,
    },
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50, // Price is down from anchor
  },
};

export const HighCashAllocation: Story = {
  args: {
    position: {
      ...basePosition,
      qty: 50,
      cash: 15000,
    },
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50,
  },
};

export const HighStockAllocation: Story = {
  args: {
    position: {
      ...basePosition,
      qty: 200,
      cash: 2000,
    },
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    config: baseConfig,
    initialPrice: 185.50,
  },
};

export const WithoutConfig: Story = {
  args: {
    position: basePosition,
    portfolioId: 'portfolio-1',
    tenantId: 'tenant-1',
    initialPrice: 185.50,
  },
};
