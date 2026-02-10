import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import ConfirmDialog from './ConfirmDialog';
import { Button } from '../ui/button';

const meta: Meta<typeof ConfirmDialog> = {
  title: 'Shared/ConfirmDialog',
  component: ConfirmDialog,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['danger', 'warning', 'info'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Danger: Story = {
  args: {
    isOpen: true,
    title: 'Delete Position',
    message: 'Are you sure you want to delete this position? This action cannot be undone.',
    confirmLabel: 'Delete',
    cancelLabel: 'Cancel',
    variant: 'danger',
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled'),
  },
};

export const Warning: Story = {
  args: {
    isOpen: true,
    title: 'Pause Trading',
    message: 'Pausing will stop all automated trading for this position. You can resume at any time.',
    confirmLabel: 'Pause Trading',
    cancelLabel: 'Keep Active',
    variant: 'warning',
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled'),
  },
};

export const Info: Story = {
  args: {
    isOpen: true,
    title: 'Reset Anchor Price',
    message: 'This will set the anchor price to the current market price. All trigger calculations will use the new anchor.',
    confirmLabel: 'Reset Anchor',
    cancelLabel: 'Cancel',
    variant: 'info',
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled'),
  },
};

export const LongMessage: Story = {
  args: {
    isOpen: true,
    title: 'Confirm Trade Execution',
    message: `You are about to execute the following trade:

Action: SELL
Quantity: 50 shares
Estimated Price: $185.50
Estimated Commission: $0.19
Total Proceeds: $9,274.81

This action will be logged to the audit trail.`,
    confirmLabel: 'Execute Trade',
    cancelLabel: 'Cancel',
    variant: 'warning',
    onConfirm: () => console.log('Confirmed'),
    onCancel: () => console.log('Cancelled'),
  },
};

// Interactive example with button trigger
const InteractiveExample = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [lastAction, setLastAction] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <Button onClick={() => setIsOpen(true)} variant="destructive">
        Delete Position
      </Button>

      {lastAction && (
        <p className="text-sm text-gray-600">Last action: {lastAction}</p>
      )}

      <ConfirmDialog
        isOpen={isOpen}
        title="Delete Position"
        message="Are you sure you want to delete this position? This action cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={() => {
          setLastAction('Confirmed deletion');
          setIsOpen(false);
        }}
        onCancel={() => {
          setLastAction('Cancelled');
          setIsOpen(false);
        }}
      />
    </div>
  );
};

export const Interactive: Story = {
  render: () => <InteractiveExample />,
};
