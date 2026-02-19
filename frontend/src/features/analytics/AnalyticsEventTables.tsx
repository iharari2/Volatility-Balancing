import { useState, useMemo } from 'react';
import { Download, FileSpreadsheet, ArrowUpDown, TrendingUp, DollarSign } from 'lucide-react';
import toast from 'react-hot-toast';
import type { AnalyticsEvent } from '../../services/portfolioScopedApi';
import { exportToExcel } from '../../utils/exportExcel';

interface AnalyticsEventTablesProps {
  events: AnalyticsEvent[];
}

type SortDirection = 'asc' | 'desc';
type TradesSortField = 'date' | 'asset_symbol' | 'side' | 'qty' | 'price' | 'total' | 'commission';
type DividendsSortField = 'date' | 'asset_symbol' | 'shares_held' | 'dps' | 'gross_amount' | 'net_amount';

export default function AnalyticsEventTables({ events }: AnalyticsEventTablesProps) {
  const [activeTab, setActiveTab] = useState<'trades' | 'dividends'>('trades');
  const [tradesSortField, setTradesSortField] = useState<TradesSortField>('date');
  const [tradesSortDir, setTradesSortDir] = useState<SortDirection>('desc');
  const [dividendsSortField, setDividendsSortField] = useState<DividendsSortField>('date');
  const [dividendsSortDir, setDividendsSortDir] = useState<SortDirection>('desc');

  // Separate trades and dividends
  const tradeEvents = useMemo(() => {
    return events.filter((e) => e.type === 'TRADE');
  }, [events]);

  const dividendEvents = useMemo(() => {
    return events.filter((e) => e.type === 'DIVIDEND');
  }, [events]);

  // Sorted trades
  const sortedTrades = useMemo(() => {
    const sorted = [...tradeEvents].sort((a, b) => {
      let aVal: any, bVal: any;
      switch (tradesSortField) {
        case 'date':
          aVal = a.date;
          bVal = b.date;
          break;
        case 'asset_symbol':
          aVal = a.asset_symbol || '';
          bVal = b.asset_symbol || '';
          break;
        case 'side':
          aVal = a.side || '';
          bVal = b.side || '';
          break;
        case 'qty':
          aVal = a.qty || 0;
          bVal = b.qty || 0;
          break;
        case 'price':
          aVal = a.price || 0;
          bVal = b.price || 0;
          break;
        case 'total':
          aVal = (a.qty || 0) * (a.price || 0);
          bVal = (b.qty || 0) * (b.price || 0);
          break;
        case 'commission':
          aVal = a.commission || 0;
          bVal = b.commission || 0;
          break;
        default:
          aVal = a.date;
          bVal = b.date;
      }
      if (aVal < bVal) return tradesSortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return tradesSortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [tradeEvents, tradesSortField, tradesSortDir]);

  // Sorted dividends
  const sortedDividends = useMemo(() => {
    const sorted = [...dividendEvents].sort((a, b) => {
      let aVal: any, bVal: any;
      switch (dividendsSortField) {
        case 'date':
          aVal = a.date;
          bVal = b.date;
          break;
        case 'asset_symbol':
          aVal = a.asset_symbol || '';
          bVal = b.asset_symbol || '';
          break;
        case 'shares_held':
          aVal = a.shares_held || 0;
          bVal = b.shares_held || 0;
          break;
        case 'dps':
          aVal = a.dps || 0;
          bVal = b.dps || 0;
          break;
        case 'gross_amount':
          aVal = a.gross_amount || 0;
          bVal = b.gross_amount || 0;
          break;
        case 'net_amount':
          aVal = a.net_amount || 0;
          bVal = b.net_amount || 0;
          break;
        default:
          aVal = a.date;
          bVal = b.date;
      }
      if (aVal < bVal) return dividendsSortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return dividendsSortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [dividendEvents, dividendsSortField, dividendsSortDir]);

  // Toggle sort for trades
  const handleTradesSort = (field: TradesSortField) => {
    if (tradesSortField === field) {
      setTradesSortDir(tradesSortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setTradesSortField(field);
      setTradesSortDir('desc');
    }
  };

  // Toggle sort for dividends
  const handleDividendsSort = (field: DividendsSortField) => {
    if (dividendsSortField === field) {
      setDividendsSortDir(dividendsSortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setDividendsSortField(field);
      setDividendsSortDir('desc');
    }
  };

  // Export trades to CSV
  const exportTradesToCsv = () => {
    const headers = ['Date', 'Symbol', 'Action', 'Quantity', 'Price', 'Total Value', 'Commission'];
    const rows = sortedTrades.map((t) => [
      t.date,
      t.asset_symbol || '',
      t.side || '',
      t.qty?.toString() || '0',
      t.price?.toFixed(2) || '0.00',
      ((t.qty || 0) * (t.price || 0)).toFixed(2),
      t.commission?.toFixed(2) || '0.00',
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    downloadCsv(csvContent, 'trades.csv');
  };

  // Export dividends to CSV
  const exportDividendsToCsv = () => {
    const headers = ['Ex-Dividend Date', 'Symbol', 'Shares Held', 'DPS', 'Gross Amount', 'Withholding Tax', 'Net Amount'];
    const rows = sortedDividends.map((d) => {
      const gross = d.gross_amount || 0;
      const net = d.net_amount || 0;
      const tax = gross - net;
      return [
        d.date,
        d.asset_symbol || '',
        d.shares_held?.toString() || '0',
        d.dps?.toFixed(4) || '0.0000',
        gross.toFixed(2),
        tax.toFixed(2),
        net.toFixed(2),
      ];
    });

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    downloadCsv(csvContent, 'dividends.csv');
  };

  const downloadCsv = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  // Summary stats
  const tradesSummary = useMemo(() => {
    const buys = tradeEvents.filter((t) => t.side === 'BUY');
    const sells = tradeEvents.filter((t) => t.side === 'SELL');
    const totalCommission = tradeEvents.reduce((sum, t) => sum + (t.commission || 0), 0);
    const totalVolume = tradeEvents.reduce((sum, t) => sum + (t.qty || 0) * (t.price || 0), 0);
    return { buys: buys.length, sells: sells.length, totalCommission, totalVolume };
  }, [tradeEvents]);

  const dividendsSummary = useMemo(() => {
    const totalGross = dividendEvents.reduce((sum, d) => sum + (d.gross_amount || 0), 0);
    const totalNet = dividendEvents.reduce((sum, d) => sum + (d.net_amount || 0), 0);
    const totalTax = totalGross - totalNet;
    return { count: dividendEvents.length, totalGross, totalNet, totalTax };
  }, [dividendEvents]);

  const SortableHeader = ({
    label,
    field,
    currentField,
    currentDir,
    onClick,
  }: {
    label: string;
    field: string;
    currentField: string;
    currentDir: SortDirection;
    onClick: () => void;
  }) => (
    <th
      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
      onClick={onClick}
    >
      <div className="flex items-center gap-1">
        {label}
        <ArrowUpDown
          className={`h-3 w-3 ${currentField === field ? 'text-blue-600' : 'text-gray-300'}`}
        />
        {currentField === field && (
          <span className="text-xs text-blue-600">{currentDir === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </th>
  );

  return (
    <div className="card">
      {/* Tab Header */}
      <div className="flex items-center justify-between border-b border-gray-200 mb-4">
        <div className="flex">
          <button
            onClick={() => setActiveTab('trades')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'trades'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Trades ({tradeEvents.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('dividends')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'dividends'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Dividends ({dividendEvents.length})
            </div>
          </button>
        </div>
        <div className="flex gap-2">
          <button
            onClick={activeTab === 'trades' ? exportTradesToCsv : exportDividendsToCsv}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            disabled={activeTab === 'trades' ? tradeEvents.length === 0 : dividendEvents.length === 0}
          >
            <Download className="h-3 w-3 mr-1" />
            CSV
          </button>
          <button
            onClick={async () => {
              try {
                await exportToExcel(
                  '/v1/excel/trading/export?format=xlsx',
                  `trading_${new Date().toISOString().split('T')[0]}.xlsx`,
                );
                toast.success('Excel exported');
              } catch (err) {
                toast.error(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
              }
            }}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <FileSpreadsheet className="h-3 w-3 mr-1" />
            Excel
          </button>
        </div>
      </div>

      {/* Trades Tab */}
      {activeTab === 'trades' && (
        <div>
          {/* Summary Stats */}
          {tradeEvents.length > 0 && (
            <div className="flex gap-4 mb-4 text-xs text-gray-600">
              <span className="bg-green-50 text-green-700 px-2 py-1 rounded">
                {tradesSummary.buys} Buys
              </span>
              <span className="bg-red-50 text-red-700 px-2 py-1 rounded">
                {tradesSummary.sells} Sells
              </span>
              <span className="bg-gray-50 text-gray-700 px-2 py-1 rounded">
                Volume: ${tradesSummary.totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
              <span className="bg-gray-50 text-gray-700 px-2 py-1 rounded">
                Commission: ${tradesSummary.totalCommission.toFixed(2)}
              </span>
            </div>
          )}

          {tradeEvents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No trade events in selected period</p>
            </div>
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <SortableHeader
                      label="Date"
                      field="date"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('date')}
                    />
                    <SortableHeader
                      label="Symbol"
                      field="asset_symbol"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('asset_symbol')}
                    />
                    <SortableHeader
                      label="Action"
                      field="side"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('side')}
                    />
                    <SortableHeader
                      label="Quantity"
                      field="qty"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('qty')}
                    />
                    <SortableHeader
                      label="Price"
                      field="price"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('price')}
                    />
                    <SortableHeader
                      label="Total Value"
                      field="total"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('total')}
                    />
                    <SortableHeader
                      label="Commission"
                      field="commission"
                      currentField={tradesSortField}
                      currentDir={tradesSortDir}
                      onClick={() => handleTradesSort('commission')}
                    />
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedTrades.map((trade, index) => {
                    const total = (trade.qty || 0) * (trade.price || 0);
                    return (
                      <tr key={`${trade.date}-${trade.asset_symbol}-${index}`} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {trade.date}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          {trade.asset_symbol || '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              trade.side === 'BUY'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {trade.side}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          {trade.qty?.toLocaleString() || 0}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          ${trade.price?.toFixed(2) || '0.00'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          ${total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                          ${trade.commission?.toFixed(2) || '0.00'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Dividends Tab */}
      {activeTab === 'dividends' && (
        <div>
          {/* Summary Stats */}
          {dividendEvents.length > 0 && (
            <div className="flex gap-4 mb-4 text-xs text-gray-600">
              <span className="bg-purple-50 text-purple-700 px-2 py-1 rounded">
                {dividendsSummary.count} Payments
              </span>
              <span className="bg-gray-50 text-gray-700 px-2 py-1 rounded">
                Gross: ${dividendsSummary.totalGross.toFixed(2)}
              </span>
              <span className="bg-red-50 text-red-700 px-2 py-1 rounded">
                Tax: ${dividendsSummary.totalTax.toFixed(2)}
              </span>
              <span className="bg-green-50 text-green-700 px-2 py-1 rounded">
                Net: ${dividendsSummary.totalNet.toFixed(2)}
              </span>
            </div>
          )}

          {dividendEvents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DollarSign className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No dividend events in selected period</p>
            </div>
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <SortableHeader
                      label="Ex-Div Date"
                      field="date"
                      currentField={dividendsSortField}
                      currentDir={dividendsSortDir}
                      onClick={() => handleDividendsSort('date')}
                    />
                    <SortableHeader
                      label="Symbol"
                      field="asset_symbol"
                      currentField={dividendsSortField}
                      currentDir={dividendsSortDir}
                      onClick={() => handleDividendsSort('asset_symbol')}
                    />
                    <SortableHeader
                      label="Shares Held"
                      field="shares_held"
                      currentField={dividendsSortField}
                      currentDir={dividendsSortDir}
                      onClick={() => handleDividendsSort('shares_held')}
                    />
                    <SortableHeader
                      label="DPS"
                      field="dps"
                      currentField={dividendsSortField}
                      currentDir={dividendsSortDir}
                      onClick={() => handleDividendsSort('dps')}
                    />
                    <SortableHeader
                      label="Gross Amount"
                      field="gross_amount"
                      currentField={dividendsSortField}
                      currentDir={dividendsSortDir}
                      onClick={() => handleDividendsSort('gross_amount')}
                    />
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Withholding Tax
                    </th>
                    <SortableHeader
                      label="Net Amount"
                      field="net_amount"
                      currentField={dividendsSortField}
                      currentDir={dividendsSortDir}
                      onClick={() => handleDividendsSort('net_amount')}
                    />
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedDividends.map((div, index) => {
                    const gross = div.gross_amount || 0;
                    const net = div.net_amount || 0;
                    const tax = gross - net;
                    return (
                      <tr key={`${div.date}-${div.asset_symbol}-${index}`} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {div.date}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          {div.asset_symbol || '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          {div.shares_held?.toLocaleString() || 0}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          ${div.dps?.toFixed(4) || '0.0000'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          ${gross.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-red-600 text-right">
                          -${tax.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-green-600 font-medium text-right">
                          ${net.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
