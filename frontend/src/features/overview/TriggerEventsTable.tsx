import { useState, useEffect } from 'react';
import { useTenantPortfolio } from '../../contexts/TenantPortfolioContext';
import { portfolioApi, positionsApi } from '../../lib/api';
import { Event } from '../../types';

interface TriggerEvent {
  id: string;
  time: string;
  type: 'Trigger' | 'Guardrail' | 'Other';
  detail: string;
}

function classifyEventType(eventType: string): 'Trigger' | 'Guardrail' | 'Other' {
  const lower = eventType.toLowerCase();
  if (lower.includes('trigger') || lower.includes('evaluate') || lower.includes('price_change')) {
    return 'Trigger';
  }
  if (lower.includes('guardrail') || lower.includes('reject') || lower.includes('breach')) {
    return 'Guardrail';
  }
  return 'Other';
}

export default function TriggerEventsTable() {
  const { selectedTenantId, selectedPortfolioId } = useTenantPortfolio();
  const [events, setEvents] = useState<TriggerEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedTenantId || !selectedPortfolioId) {
      setEvents([]);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchEvents() {
      setLoading(true);
      try {
        const positions = await portfolioApi.getPositions(selectedTenantId!, selectedPortfolioId!);

        const allEvents: Event[] = [];
        await Promise.all(
          positions.map(async (pos) => {
            try {
              const resp = await positionsApi.getEvents(pos.id, 20);
              for (const e of resp.events) {
                allEvents.push(e);
              }
            } catch {
              // skip positions with no events
            }
          }),
        );

        if (cancelled) return;

        allEvents.sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime());

        const mapped: TriggerEvent[] = allEvents.slice(0, 10).map((e) => {
          const dt = new Date(e.ts);
          return {
            id: e.id,
            time: dt.toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            }),
            type: classifyEventType(e.type),
            detail: e.message,
          };
        });

        setEvents(mapped);
      } catch (err) {
        console.error('Failed to fetch trigger events:', err);
        setEvents([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchEvents();
    return () => {
      cancelled = true;
    };
  }, [selectedTenantId, selectedPortfolioId]);

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
                      : event.type === 'Guardrail'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-gray-100 text-gray-800'
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
