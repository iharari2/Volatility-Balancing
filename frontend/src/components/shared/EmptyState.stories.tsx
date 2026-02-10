import type { Meta, StoryObj } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';
import { TrendingUp, FileText, AlertCircle } from 'lucide-react';
import EmptyState from './EmptyState';

const meta: Meta<typeof EmptyState> = {
  title: 'Shared/EmptyState',
  component: EmptyState,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div style={{ width: '500px' }}>
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: 'No positions yet',
    description: 'Get started by creating your first position to begin tracking volatility.',
  },
};

export const WithLinkAction: Story = {
  args: {
    title: 'No portfolios found',
    description: 'Create a portfolio to organize your positions and track performance.',
    action: {
      label: 'Create Portfolio',
      to: '/portfolios/new',
    },
  },
};

export const WithClickAction: Story = {
  args: {
    title: 'No simulations',
    description: 'Run a simulation to backtest your trading strategy on historical data.',
    action: {
      label: 'Run Simulation',
      onClick: () => alert('Simulation started!'),
    },
  },
};

export const WithCustomIcon: Story = {
  args: {
    icon: <TrendingUp className="h-16 w-16 text-green-400" />,
    title: 'No trades yet',
    description: 'Trades will appear here once your positions trigger buy or sell orders.',
  },
};

export const NoResults: Story = {
  args: {
    icon: <FileText className="h-16 w-16 text-gray-400" />,
    title: 'No results found',
    description: 'Try adjusting your search criteria or filters.',
  },
};

export const ErrorState: Story = {
  args: {
    icon: <AlertCircle className="h-16 w-16 text-red-400" />,
    title: 'Unable to load data',
    description: 'There was a problem connecting to the server. Please try again.',
    action: {
      label: 'Retry',
      onClick: () => alert('Retrying...'),
    },
  },
};
