import type { Meta, StoryObj } from '@storybook/react';
import EventTimeline from './EventTimeline';

const meta: Meta<typeof EventTimeline> = {
  title: 'Components/EventTimeline',
  component: EventTimeline,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

const mockEvents = [
  {
    id: 'evt-1',
    position_id: 'pos-123',
    type: 'order_filled',
    message: 'Buy order filled: 10 shares at $184.25',
    inputs: {
      order_id: 'ord-456',
      side: 'BUY',
      qty: 10,
    },
    outputs: {
      fill_price: 184.25,
      commission: 0.18,
      total_cost: 1842.68,
    },
    ts: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
  },
  {
    id: 'evt-2',
    position_id: 'pos-123',
    type: 'trigger_detected',
    message: 'Buy trigger detected: price dropped 3.2% from anchor',
    inputs: {
      current_price: 184.25,
      anchor_price: 190.35,
      threshold_pct: 3.0,
    },
    outputs: {
      price_change_pct: -3.2,
      action: 'BUY',
    },
    ts: new Date(Date.now() - 1000 * 60 * 6).toISOString(), // 6 minutes ago
  },
  {
    id: 'evt-3',
    position_id: 'pos-123',
    type: 'anchor_set',
    message: 'Anchor price set to $190.35',
    inputs: {
      new_anchor: 190.35,
      source: 'market_price',
    },
    outputs: {},
    ts: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
  },
  {
    id: 'evt-4',
    position_id: 'pos-123',
    type: 'position_created',
    message: 'Position created with 100 shares and $5,000 cash',
    inputs: {
      asset: 'AAPL',
      qty: 100,
      cash: 5000,
    },
    outputs: {
      position_id: 'pos-123',
    },
    ts: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
  },
];

export const Default: Story = {
  args: {
    events: mockEvents,
  },
};

export const Empty: Story = {
  args: {
    events: [],
  },
};

export const SingleEvent: Story = {
  args: {
    events: [mockEvents[0]],
  },
};

export const TradingActivity: Story = {
  args: {
    events: [
      {
        id: 'evt-1',
        position_id: 'pos-123',
        type: 'order_filled',
        message: 'Sell order filled: 15 shares at $192.50',
        inputs: { side: 'SELL', qty: 15 },
        outputs: { fill_price: 192.50, commission: 0.29 },
        ts: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
      },
      {
        id: 'evt-2',
        position_id: 'pos-123',
        type: 'order_submitted',
        message: 'Sell order submitted: 15 shares',
        inputs: { side: 'SELL', qty: 15 },
        outputs: { order_id: 'ord-789' },
        ts: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
      },
      {
        id: 'evt-3',
        position_id: 'pos-123',
        type: 'trigger_detected',
        message: 'Sell trigger detected: price rose 3.5% from anchor',
        inputs: { current_price: 192.50, anchor_price: 186.00 },
        outputs: { price_change_pct: 3.5, action: 'SELL' },
        ts: new Date(Date.now() - 1000 * 60 * 4).toISOString(),
      },
      {
        id: 'evt-4',
        position_id: 'pos-123',
        type: 'order_filled',
        message: 'Buy order filled: 20 shares at $183.00',
        inputs: { side: 'BUY', qty: 20 },
        outputs: { fill_price: 183.00, commission: 0.37 },
        ts: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      },
    ],
  },
};

export const WithErrors: Story = {
  args: {
    events: [
      {
        id: 'evt-1',
        position_id: 'pos-123',
        type: 'order_rejected',
        message: 'Order rejected: insufficient cash for purchase',
        inputs: { side: 'BUY', qty: 100, estimated_cost: 18500 },
        outputs: { reason: 'INSUFFICIENT_FUNDS', available_cash: 5000 },
        ts: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
      },
      {
        id: 'evt-2',
        position_id: 'pos-123',
        type: 'order_cancelled',
        message: 'Order cancelled by user',
        inputs: { order_id: 'ord-123' },
        outputs: { cancelled_at: new Date().toISOString() },
        ts: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      },
      {
        id: 'evt-3',
        position_id: 'pos-123',
        type: 'position_created',
        message: 'Position created',
        inputs: { asset: 'AAPL', qty: 50, cash: 5000 },
        outputs: {},
        ts: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      },
    ],
  },
};

export const ManyEvents: Story = {
  args: {
    events: Array.from({ length: 20 }, (_, i) => ({
      id: `evt-${i}`,
      position_id: 'pos-123',
      type: i % 4 === 0 ? 'order_filled' : i % 4 === 1 ? 'trigger_detected' : i % 4 === 2 ? 'order_submitted' : 'anchor_set',
      message: `Event ${i + 1} description`,
      inputs: { index: i },
      outputs: { result: 'success' },
      ts: new Date(Date.now() - 1000 * 60 * 60 * i).toISOString(),
    })),
  },
};
