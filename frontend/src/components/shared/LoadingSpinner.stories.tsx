import type { Meta, StoryObj } from '@storybook/react';
import LoadingSpinner from './LoadingSpinner';

const meta: Meta<typeof LoadingSpinner> = {
  title: 'Shared/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    message: 'Loading...',
    size: 'medium',
  },
};

export const Small: Story = {
  args: {
    message: 'Loading data...',
    size: 'small',
  },
};

export const Large: Story = {
  args: {
    message: 'Fetching positions...',
    size: 'large',
  },
};

export const CustomMessage: Story = {
  args: {
    message: 'Running simulation...',
    size: 'medium',
  },
};
