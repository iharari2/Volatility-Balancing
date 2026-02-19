import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Download, FileSpreadsheet, Loader2 } from 'lucide-react';

interface ExcelExportIntegrationProps {
  className?: string;
}

interface ExportStatus {
  [key: string]: 'idle' | 'loading' | 'success' | 'error';
}

const ExcelExportIntegration: React.FC<ExcelExportIntegrationProps> = ({ className }) => {
  const [exportStatus, setExportStatus] = useState<ExportStatus>({});
  const [lastExport, setLastExport] = useState<string | null>(null);

  const API_BASE = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/v1/excel`;

  const exportData = async (endpoint: string, exportName: string) => {
    setExportStatus((prev) => ({ ...prev, [exportName]: 'loading' }));

    try {
      const response = await fetch(`${API_BASE}${endpoint}`);

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${exportName}_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setExportStatus((prev) => ({ ...prev, [exportName]: 'success' }));
        setLastExport(exportName);

        // Reset status after 3 seconds
        setTimeout(() => {
          setExportStatus((prev) => ({ ...prev, [exportName]: 'idle' }));
        }, 3000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Export failed');
      }
    } catch (error) {
      console.error(`Export error for ${exportName}:`, error);
      setExportStatus((prev) => ({ ...prev, [exportName]: 'error' }));

      // Reset status after 5 seconds
      setTimeout(() => {
        setExportStatus((prev) => ({ ...prev, [exportName]: 'idle' }));
      }, 5000);
    }
  };

  const exportButtons = [
    {
      name: 'positions',
      label: 'Positions',
      description: 'Export all current positions',
      endpoint: '/positions/export',
      icon: '📋',
    },
    {
      name: 'trades',
      label: 'Trades',
      description: 'Export trade history',
      endpoint: '/trades/export',
      icon: '🔄',
    },
    {
      name: 'orders',
      label: 'Orders',
      description: 'Export order history',
      endpoint: '/orders/export',
      icon: '📝',
    },
    {
      name: 'trading',
      label: 'Trading Data',
      description: 'Export all trading data',
      endpoint: '/trading/export',
      icon: '💼',
    },
    {
      name: 'simulation',
      label: 'Simulation',
      description: 'Export simulation results',
      endpoint: '/simulation/test-simulation/export',
      icon: '📊',
    },
    {
      name: 'optimization',
      label: 'Optimization',
      description: 'Export optimization results',
      endpoint: '/optimization/test-config/export',
      icon: '📈',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'loading':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'success':
        return <div className="h-4 w-4 rounded-full bg-green-500" />;
      case 'error':
        return <div className="h-4 w-4 rounded-full bg-red-500" />;
      default:
        return <FileSpreadsheet className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'loading':
        return 'Exporting...';
      case 'success':
        return 'Exported!';
      case 'error':
        return 'Failed';
      default:
        return 'Export';
    }
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Excel Export
          </CardTitle>
          <CardDescription>
            Export your data to Excel format for analysis and reporting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {exportButtons.map((button) => (
              <div key={button.name} className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{button.icon}</span>
                  <h3 className="font-medium">{button.label}</h3>
                </div>
                <p className="text-sm text-muted-foreground">{button.description}</p>
                <Button
                  onClick={() => exportData(button.endpoint, button.name)}
                  disabled={exportStatus[button.name] === 'loading'}
                  className="w-full"
                  variant={exportStatus[button.name] === 'success' ? 'default' : 'outline'}
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(exportStatus[button.name])}
                    {getStatusText(exportStatus[button.name])}
                  </div>
                </Button>
              </div>
            ))}
          </div>

          {lastExport && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-sm text-green-800">
                ✅ Successfully exported {lastExport} data to Excel
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ExcelExportIntegration;
