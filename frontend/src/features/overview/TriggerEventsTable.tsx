import { useState, useEffect } from 'react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';

interface TriggerEvent {
  id: string;
  time: string;
  type: 'Trigger' | 'Guardrail';
  detail: string;
}

export default function TriggerEventsTable() {
  const { selectedPortfolioId } = useTenantPortfolio();
  const [events, setEvents] = useState<TriggerEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedPortfolioId) {
      setLoading(false);
      return;
    }

    // TODO: Fetch trigger events from API
    // For now, use mock data
    const mockEvents: TriggerEvent[] = [
      {
        id: '1',
        time: '10:03',
        type: 'Trigger',
        detail: 'BUY signal fired (−3.1%)',
      },
      {
        id: '2',
        time: '10:03',
        type: 'Guardrail',
        detail: 'Allowed trade (stock%=49→52)',
      },
    ];
    setEvents(mockEvents);
    setLoading(false);
  }, [selectedPortfolioId]);

  if (loading) {
    return <p className="text-sm text-gray-500">Loading events...</p>;
  }

  if (events.length === 0) {
    return <p className="text-sm text-gray-500">No trigger events</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Detail
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {events.map((event) => (
            <tr key={event.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{event.time}</td>
              <td className="px-4 py-3 whitespace-nowrap text-sm">
                <span
                  className={`badge ${
                    event.type === 'Trigger'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-purple-100 text-purple-800'
                  }`}
                >
                  {event.type}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-900">{event.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}







