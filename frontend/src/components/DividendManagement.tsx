import {
  useDividendPositionStatus,
  useProcessDividendPayment,
  useDividendMarketInfo,
  useUpcomingDividends,
} from '../hooks/useDividends';
import { DollarSign, Calendar, TrendingUp, AlertCircle, Play, Download, Clock } from 'lucide-react';
import { format, isPast, parseISO } from 'date-fns';
import toast from 'react-hot-toast';
import { exportToExcel } from '../utils/exportExcel';

interface DividendManagementProps {
  tenantId: string;
  portfolioId: string;
  positionId: string;
  ticker: string;
}

function fmt$(n: number) {
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function DividendManagement({ tenantId, portfolioId, positionId, ticker }: DividendManagementProps) {
  const { data: positionStatus, isLoading: statusLoading } =
    useDividendPositionStatus(tenantId, portfolioId, positionId);
  const { data: marketInfo, isLoading: marketLoading } = useDividendMarketInfo(ticker);
  const { data: upcoming, isLoading: upcomingLoading } = useUpcomingDividends(ticker);

  const processPayment = useProcessDividendPayment(tenantId, portfolioId, positionId);

  const handleProcessPayment = async (receivableId: string) => {
    try {
      await processPayment.mutateAsync(receivableId);
      toast.success('Payment processed');
    } catch {
      toast.error('Failed to process payment');
    }
  };

  const loading = statusLoading || marketLoading || upcomingLoading;

  // ── Build upcoming events ────────────────────────────────────────────────
  const upcomingEvents: { ex_date: string; pay_date: string; dps: number; currency?: string; source: 'market' }[] = [];

  if (upcoming?.upcoming_dividends) {
    for (const d of upcoming.upcoming_dividends) {
      upcomingEvents.push({ ...d, source: 'market' });
    }
  }
  // Also add next from marketInfo if not already covered
  if (marketInfo?.next_ex_date && marketInfo?.next_dps) {
    const alreadyIn = upcomingEvents.some((e) => e.ex_date === marketInfo.next_ex_date);
    if (!alreadyIn) {
      upcomingEvents.push({
        ex_date: marketInfo.next_ex_date,
        pay_date: marketInfo.next_pay_date ?? marketInfo.next_ex_date,
        dps: marketInfo.next_dps,
        source: 'market',
      });
    }
  }
  upcomingEvents.sort((a, b) => a.ex_date.localeCompare(b.ex_date));

  // ── Build history: past ex-div records + paid/pending receivables ────────
  const pastDividends: { id: string; ex_date: string; dps: number; type: 'ex-div' }[] =
    (positionStatus?.recent_dividends ?? []).map((d: any) => ({
      id: d.id,
      ex_date: d.ex_date,
      dps: d.dps,
      type: 'ex-div',
    }));

  const pendingReceivables: { id: string; net_amount: number; pay_date: string; status: 'pending' }[] =
    (positionStatus?.pending_receivables ?? []).map((r: any) => ({
      id: r.id,
      net_amount: r.net_amount,
      pay_date: r.pay_date,
      status: 'pending',
    }));

  const hasPending = pendingReceivables.length > 0;
  const hasHistory = pastDividends.length > 0;
  const hasUpcoming = upcomingEvents.length > 0;

  return (
    <div className="space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-gray-900">Dividends — {ticker}</h3>
          {marketInfo?.dividend_frequency && (
            <p className="text-xs text-gray-400 mt-0.5">Frequency: {marketInfo.dividend_frequency}</p>
          )}
        </div>
        <button
          onClick={async () => {
            try {
              await exportToExcel(
                `/v1/excel/dividends/export?tenant_id=${tenantId}&portfolio_id=${portfolioId}&position_id=${positionId}`,
                `dividends_${ticker}_${new Date().toISOString().split('T')[0]}.xlsx`,
              );
              toast.success('Exported');
            } catch (err) {
              toast.error(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
            }
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
        >
          <Download className="h-3.5 w-3.5" /> Excel
        </button>
      </div>

      {loading && (
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3].map((i) => <div key={i} className="h-10 bg-gray-100 rounded-lg" />)}
        </div>
      )}

      {!loading && (
        <>
          {/* ── Pending receivables (action required) ── */}
          {hasPending && (
            <div className="border border-amber-200 bg-amber-50 rounded-lg overflow-hidden">
              <div className="px-4 py-2 bg-amber-100 border-b border-amber-200">
                <span className="text-xs font-bold text-amber-800 uppercase tracking-wide">
                  Pending Payment
                </span>
              </div>
              <div className="divide-y divide-amber-100">
                {pendingReceivables.map((r) => (
                  <div key={r.id} className="flex items-center justify-between px-4 py-3">
                    <div className="flex items-center gap-3">
                      <DollarSign className="h-4 w-4 text-amber-600 flex-shrink-0" />
                      <div>
                        <div className="text-sm font-semibold text-gray-900">{fmt$(r.net_amount)} net</div>
                        <div className="text-xs text-gray-500">
                          Pay date: {format(parseISO(r.pay_date), 'MMM d, yyyy')}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleProcessPayment(r.id)}
                      disabled={processPayment.isPending}
                      className="flex items-center gap-1 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
                    >
                      <Play className="h-3 w-3" /> Process
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Upcoming dividends ── */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-indigo-500" />
              <h4 className="text-sm font-bold text-gray-700">Upcoming</h4>
            </div>
            {hasUpcoming ? (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-4 py-2 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wide">Ex-Date</th>
                      <th className="px-4 py-2 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wide">Pay Date</th>
                      <th className="px-4 py-2 text-right text-[10px] font-bold text-gray-400 uppercase tracking-wide">$/Share</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {upcomingEvents.map((d, i) => (
                      <tr key={i} className="hover:bg-indigo-50/30">
                        <td className="px-4 py-2.5 font-medium text-indigo-700">
                          {format(parseISO(d.ex_date), 'MMM d, yyyy')}
                        </td>
                        <td className="px-4 py-2.5 text-gray-600">
                          {format(parseISO(d.pay_date), 'MMM d, yyyy')}
                        </td>
                        <td className="px-4 py-2.5 text-right font-semibold text-gray-900">
                          {fmt$(d.dps)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-400 border border-dashed border-gray-200 rounded-lg">
                <Clock className="h-6 w-6 mx-auto mb-1 text-gray-300" />
                <p className="text-xs">No upcoming dividends found</p>
              </div>
            )}
          </div>

          {/* ── Past ex-div events ── */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <h4 className="text-sm font-bold text-gray-700">History</h4>
            </div>
            {hasHistory ? (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-4 py-2 text-left text-[10px] font-bold text-gray-400 uppercase tracking-wide">Ex-Date</th>
                      <th className="px-4 py-2 text-right text-[10px] font-bold text-gray-400 uppercase tracking-wide">$/Share</th>
                      <th className="px-4 py-2 text-right text-[10px] font-bold text-gray-400 uppercase tracking-wide">Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {pastDividends
                      .sort((a, b) => b.ex_date.localeCompare(a.ex_date))
                      .map((d) => (
                        <tr key={d.id} className="hover:bg-gray-50">
                          <td className="px-4 py-2.5 text-gray-700">
                            {format(parseISO(d.ex_date), 'MMM d, yyyy')}
                          </td>
                          <td className="px-4 py-2.5 text-right font-semibold text-gray-900">
                            {fmt$(d.dps)}
                          </td>
                          <td className="px-4 py-2.5 text-right">
                            <span className="text-[10px] font-semibold bg-green-50 text-green-700 border border-green-200 px-1.5 py-0.5 rounded">
                              Ex-Div
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-400 border border-dashed border-gray-200 rounded-lg">
                <AlertCircle className="h-6 w-6 mx-auto mb-1 text-gray-300" />
                <p className="text-xs">No dividend history recorded</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
