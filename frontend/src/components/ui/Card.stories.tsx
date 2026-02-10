import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card';
import { Button } from './button';
import { TrendingUp, DollarSign, PieChart } from 'lucide-react';

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content with some text inside.</p>
      </CardContent>
    </Card>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Position Summary</CardTitle>
        <CardDescription>AAPL - Apple Inc.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-500">Shares</span>
            <span className="font-medium">100</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Value</span>
            <span className="font-medium">$18,550.00</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="justify-end space-x-2">
        <Button variant="outline">View Details</Button>
        <Button>Trade</Button>
      </CardFooter>
    </Card>
  ),
};

export const KPICard: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Value</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">$45,231.89</div>
          <p className="text-xs text-muted-foreground">+20.1% from last month</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Returns</CardTitle>
          <TrendingUp className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">+12.5%</div>
          <p className="text-xs text-muted-foreground">Since inception</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Allocation</CardTitle>
          <PieChart className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">65% / 35%</div>
          <p className="text-xs text-muted-foreground">Stock / Cash</p>
        </CardContent>
      </Card>
    </div>
  ),
};

export const PortfolioCard: Story = {
  render: () => (
    <Card className="w-[400px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Growth Portfolio</CardTitle>
            <CardDescription>High-growth tech stocks</CardDescription>
          </div>
          <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
            Active
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Total Value</span>
            <span className="text-xl font-bold">$125,430.00</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Positions</span>
            <span className="font-medium">5</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Today's P&L</span>
            <span className="font-medium text-green-600">+$1,234.56</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-500 h-2 rounded-full" style={{ width: '65%' }} />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Stock: 65%</span>
            <span>Cash: 35%</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="justify-between">
        <Button variant="outline" size="sm">Configure</Button>
        <Button size="sm">View Positions</Button>
      </CardFooter>
    </Card>
  ),
};

export const CompactCard: Story = {
  render: () => (
    <Card className="w-[250px] p-4">
      <div className="flex items-center space-x-4">
        <div className="p-2 bg-blue-100 rounded-lg">
          <TrendingUp className="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-900">AAPL</p>
          <p className="text-lg font-bold">$185.50</p>
        </div>
      </div>
    </Card>
  ),
};
