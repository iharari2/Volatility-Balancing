import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';

interface TimelineEvent {
  date: string;
  price: number;
  shares: number;
  cash: number;
  asset_allocation_pct: number;
  triggered: boolean;
  side: string | null;
}

interface GuardrailBandChartProps {
  timelineEvents: TimelineEvent[];
  minStockPct?: number;
  maxStockPct?: number;
  height?: number;
}

export default function GuardrailBandChart({
  timelineEvents,
  minStockPct = 25,
  maxStockPct = 75,
  height = 280,
}: GuardrailBandChartProps) {
  if (!timelineEvents || timelineEvents.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
        style={{ height }}
      >
        <p className="text-xs text-gray-500">No timeline data for guardrail visualization</p>
      </div>
    );
  }

  // Build chart data: price line with guardrail price bands
  const chartData = timelineEvents.map((event) => {
    const alloc = event.asset_allocation_pct;

    // Compute guardrail price thresholds given current shares & cash
    let upperPrice: number | null = null;
    let lowerPrice: number | null = null;
    if (event.shares > 0) {
      // price where stock_pct = max → shares * p / (shares * p + cash) = max
      // → p = max * cash / (shares * (1 - max))
      const maxFrac = maxStockPct / 100;
      const minFrac = minStockPct / 100;
      if (maxFrac < 1) {
        upperPrice = (maxFrac * event.cash) / (event.shares * (1 - maxFrac));
      }
      if (minFrac > 0) {
        lowerPrice = (minFrac * event.cash) / (event.shares * (1 - minFrac));
      }
    }

    return {
      date: event.date,
      price: event.price,
      upperGuardrail: upperPrice,
      lowerGuardrail: lowerPrice,
      allocation: alloc,
      buyTrigger: event.triggered && event.side === 'BUY' ? event.price : null,
      sellTrigger: event.triggered && event.side === 'SELL' ? event.price : null,
    };
  });

  return (
    <div className="space-y-4">
      {/* Price with Guardrail Bands */}
      <div>
        <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
          Price vs Guardrail Boundaries
        </h4>
        <ResponsiveContainer width="100%" height={height}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(v) => `$${v}`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: any, name: string) => {
                if (value === null || value === undefined) return ['-', name];
                const v = Number(value);
                const label =
                  name === 'price'
                    ? 'Price'
                    : name === 'upperGuardrail'
                      ? `Upper (${maxStockPct}%)`
                      : name === 'lowerGuardrail'
                        ? `Lower (${minStockPct}%)`
                        : name;
                return [`$${v.toFixed(2)}`, label];
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="upperGuardrail"
              stroke="#ef4444"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              name={`Upper (${maxStockPct}%)`}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="lowerGuardrail"
              stroke="#f97316"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              name={`Lower (${minStockPct}%)`}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              name="Price"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Allocation % over time */}
      <div>
        <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
          Stock Allocation % with Guardrail Limits
        </h4>
        <ResponsiveContainer width="100%" height={180}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)}%`,
                name === 'allocation' ? 'Stock %' : name,
              ]}
            />
            <ReferenceArea
              y1={minStockPct}
              y2={maxStockPct}
              fill="#22c55e"
              fillOpacity={0.08}
              label={{ value: 'Safe Zone', position: 'insideTopRight', fontSize: 10, fill: '#16a34a' }}
            />
            <ReferenceLine y={maxStockPct} stroke="#ef4444" strokeDasharray="5 5" label={{ value: `Max ${maxStockPct}%`, position: 'right', fontSize: 10, fill: '#ef4444' }} />
            <ReferenceLine y={minStockPct} stroke="#f97316" strokeDasharray="5 5" label={{ value: `Min ${minStockPct}%`, position: 'right', fontSize: 10, fill: '#f97316' }} />
            <Area
              type="monotone"
              dataKey="allocation"
              stroke="#2563eb"
              fill="#2563eb"
              fillOpacity={0.15}
              strokeWidth={2}
              name="Stock %"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
