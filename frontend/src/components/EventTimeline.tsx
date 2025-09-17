import { Event } from '../types';
import { format } from 'date-fns';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Target,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';

interface EventTimelineProps {
  events: Event[];
}

const getEventIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case 'position_created':
      return Activity;
    case 'anchor_set':
      return Target;
    case 'trigger_detected':
      return AlertCircle;
    case 'order_submitted':
      return TrendingUp;
    case 'order_filled':
      return CheckCircle;
    case 'order_cancelled':
    case 'order_rejected':
      return XCircle;
    default:
      return Info;
  }
};

const getEventColor = (type: string) => {
  switch (type.toLowerCase()) {
    case 'position_created':
      return 'text-primary-600 bg-primary-100';
    case 'anchor_set':
      return 'text-warning-600 bg-warning-100';
    case 'trigger_detected':
      return 'text-danger-600 bg-danger-100';
    case 'order_submitted':
      return 'text-primary-600 bg-primary-100';
    case 'order_filled':
      return 'text-success-600 bg-success-100';
    case 'order_cancelled':
    case 'order_rejected':
      return 'text-danger-600 bg-danger-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

export default function EventTimeline({ events }: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Events Yet</h3>
          <p className="text-gray-500">
            Events will appear here as you interact with the position.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Event Timeline</h3>

      <div className="flow-root">
        <ul className="-mb-8">
          {events.map((event, eventIdx) => {
            const Icon = getEventIcon(event.type);
            const colorClasses = getEventColor(event.type);

            return (
              <li key={event.id}>
                <div className="relative pb-8">
                  {eventIdx !== events.length - 1 ? (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  ) : null}
                  <div className="relative flex space-x-3">
                    <div>
                      <span
                        className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${colorClasses}`}
                      >
                        <Icon className="h-4 w-4" />
                      </span>
                    </div>
                    <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            {event.type.replace(/_/g, ' ').toUpperCase()}
                          </h4>
                          <span className="text-xs text-gray-500">
                            {format(new Date(event.ts), 'MMM d, yyyy h:mm:ss a')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{event.message}</p>

                        {event.inputs && Object.keys(event.inputs).length > 0 && (
                          <div className="mt-2">
                            <details className="text-xs">
                              <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                                View Inputs
                              </summary>
                              <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                {JSON.stringify(event.inputs, null, 2)}
                              </pre>
                            </details>
                          </div>
                        )}

                        {event.outputs && Object.keys(event.outputs).length > 0 && (
                          <div className="mt-2">
                            <details className="text-xs">
                              <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                                View Outputs
                              </summary>
                              <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                                {JSON.stringify(event.outputs, null, 2)}
                              </pre>
                            </details>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}


