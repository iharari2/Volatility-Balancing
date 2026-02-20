import { useState } from 'react';
import {
  useDividendPositionStatus,
  useProcessExDividend,
  useProcessDividendPayment,
} from '../hooks/useDividends';
import { useDividendMarketInfo, useUpcomingDividends } from '../hooks/useDividends';
import {
  DollarSign,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Play,
  Clock,
  Download,
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { exportToExcel } from '../utils/exportExcel';

interface DividendManagementProps {
  tenantId: string;
  portfolioId: string;
  positionId: string;
  ticker: string;
}

export default function DividendManagement({ tenantId, portfolioId, positionId, ticker }: DividendManagementProps) {
  const [activeTab, setActiveTab] = useState<'status' | 'market' | 'upcoming'>('status');

  const {
    data: positionStatus,
    isLoading: statusLoading,
    error: statusError,
  } = useDividendPositionStatus(tenantId, portfolioId, positionId);
  const {
    data: marketInfo,
    isLoading: marketLoading,
    error: marketError,
  } = useDividendMarketInfo(ticker);
  const {
    data: upcoming,
    isLoading: upcomingLoading,
    error: upcomingError,
  } = useUpcomingDividends(ticker);

  const processExDividend = useProcessExDividend(tenantId, portfolioId, positionId);
  const processPayment = useProcessDividendPayment(tenantId, portfolioId, positionId);

  const handleProcessExDividend = async () => {
    try {
      await processExDividend.mutateAsync();
    } catch (error) {
      console.error('Failed to process ex-dividend:', error);
    }
  };

  const handleProcessPayment = async (receivableId: string) => {
    try {
      await processPayment.mutateAsync(receivableId);
    } catch (error) {
      console.error('Failed to process payment:', error);
    }
  };

  const tabs = [
    { id: 'status', label: 'Position Status', icon: CheckCircle },
    { id: 'market', label: 'Market Info', icon: TrendingUp },
    { id: 'upcoming', label: 'Upcoming', icon: Calendar },
  ];

  // Show error state if there are critical errors
  if (statusError || marketError || upcomingError) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Dividend Management</h3>
        </div>
        <div className="card">
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">Error Loading Dividend Data</h4>
            <div className="text-sm text-gray-600 space-y-1">
              {statusError && <p>Position Status Error: {statusError.message}</p>}
              {marketError && <p>Market Info Error: {marketError.message}</p>}
              {upcomingError && <p>Upcoming Dividends Error: {upcomingError.message}</p>}
            </div>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 btn btn-primary btn-sm"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900">Dividend Management</h3>
          <button
            onClick={async () => {
              try {
                await exportToExcel(
                  `/v1/excel/dividends/export?tenant_id=${tenantId}&portfolio_id=${portfolioId}&position_id=${positionId}`,
                  `dividends_${ticker}_${new Date().toISOString().split('T')[0]}.xlsx`,
                );
                toast.success('Dividends exported');
              } catch (err) {
                toast.error(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            title="Export to Excel"
          >
            <Download className="h-4 w-4" />
            Excel
          </button>
        </div>
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-1 px-3 py-1 text-sm rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="card">
        {activeTab === 'status' && (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Position Dividend Status</h4>

            {statusLoading ? (
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ) : positionStatus ? (
              <div className="space-y-4">
                {/* Pending Receivables */}
                {positionStatus.pending_receivables &&
                positionStatus.pending_receivables.length > 0 ? (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Pending Receivables</h5>
                    <div className="space-y-2">
                      {positionStatus.pending_receivables.map((receivable) => (
                        <div
                          key={receivable.id}
                          className="flex items-center justify-between p-3 bg-warning-50 border border-warning-200 rounded-lg"
                        >
                          <div className="flex items-center space-x-3">
                            <DollarSign className="w-5 h-5 text-warning-600" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                ${receivable.net_amount.toFixed(2)} (net)
                              </div>
                              <div className="text-xs text-gray-500">
                                Pay date: {format(new Date(receivable.pay_date), 'MMM dd, yyyy')}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleProcessPayment(receivable.id)}
                            disabled={processPayment.isPending}
                            className="btn btn-sm btn-primary"
                          >
                            <Play className="w-3 h-3 mr-1" />
                            Process
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm">No pending receivables</p>
                  </div>
                )}

                {/* Recent Dividends */}
                {positionStatus.recent_dividends && positionStatus.recent_dividends.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Recent Dividends</h5>
                    <div className="space-y-1">
                      {positionStatus.recent_dividends.slice(0, 3).map((dividend) => (
                        <div
                          key={dividend.id}
                          className="flex items-center justify-between py-2 text-sm"
                        >
                          <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            <span>${dividend.dps.toFixed(2)} per share</span>
                          </div>
                          <span className="text-gray-500">
                            {format(new Date(dividend.ex_date), 'MMM dd')}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">Failed to load dividend status</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'market' && (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Market Dividend Information</h4>

            {marketLoading ? (
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ) : marketInfo ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-500">Frequency</label>
                    <p className="text-sm font-medium">{marketInfo.dividend_frequency}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">Next Ex-Date</label>
                    <p className="text-sm font-medium">
                      {marketInfo.next_ex_date
                        ? format(new Date(marketInfo.next_ex_date), 'MMM dd, yyyy')
                        : 'N/A'}
                    </p>
                  </div>
                </div>

                {marketInfo.next_dps && (
                  <div className="p-3 bg-primary-50 border border-primary-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-primary-600" />
                      <span className="text-sm font-medium text-primary-900">
                        Next Dividend: ${marketInfo.next_dps.toFixed(2)} per share
                      </span>
                    </div>
                    {marketInfo.next_pay_date && (
                      <p className="text-xs text-primary-700 mt-1">
                        Pay date: {format(new Date(marketInfo.next_pay_date), 'MMM dd, yyyy')}
                      </p>
                    )}
                  </div>
                )}

                {marketInfo.last_dividend && (
                  <div>
                    <label className="text-xs text-gray-500">Last Dividend</label>
                    <div className="text-sm">
                      ${marketInfo.last_dividend.dps.toFixed(2)} on{' '}
                      {format(new Date(marketInfo.last_dividend.ex_date), 'MMM dd, yyyy')}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">Failed to load market information</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'upcoming' && (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Upcoming Dividends</h4>

            {upcomingLoading ? (
              <div className="animate-pulse space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ) : upcoming?.upcoming_dividends && upcoming.upcoming_dividends.length > 0 ? (
              <div className="space-y-2">
                {upcoming.upcoming_dividends.map((dividend, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <Calendar className="w-5 h-5 text-gray-400" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          ${dividend.dps.toFixed(2)} per share
                        </div>
                        <div className="text-xs text-gray-500">
                          Ex: {format(new Date(dividend.ex_date), 'MMM dd, yyyy')} • Pay:{' '}
                          {format(new Date(dividend.pay_date), 'MMM dd, yyyy')}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">
                        {format(new Date(dividend.ex_date), 'MMM dd')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No upcoming dividends found</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
