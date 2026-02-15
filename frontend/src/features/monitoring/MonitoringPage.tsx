import { RefreshCw } from 'lucide-react';
import {
  useSystemStatus,
  useAlerts,
  useAcknowledgeAlert,
  useResolveAlert,
  useWebhookConfig,
  useSetWebhookConfig,
} from '../../hooks/useMonitoring';
import SystemHealthCards from './components/SystemHealthCards';
import AlertsTable from './components/AlertsTable';
import WebhookConfig from './components/WebhookConfig';

export default function MonitoringPage() {
  const { data: statusData, isLoading: statusLoading, dataUpdatedAt } = useSystemStatus();
  const { data: alertsData, isLoading: alertsLoading } = useAlerts();
  const { data: webhookData, isLoading: webhookLoading } = useWebhookConfig();

  const acknowledgeMutation = useAcknowledgeAlert();
  const resolveMutation = useResolveAlert();
  const webhookMutation = useSetWebhookConfig();

  const isLoading = statusLoading || alertsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-gray-900">Monitoring</h1>
          <p className="text-sm text-gray-500 mt-1">System health, alerts, and webhook configuration</p>
        </div>
        {dataUpdatedAt > 0 && (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <RefreshCw className="h-3 w-3" />
            <span>
              Updated {new Date(dataUpdatedAt).toLocaleTimeString()} &middot; auto-refresh 30s
            </span>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-16 text-gray-400 text-sm">Loading monitoring data...</div>
      ) : (
        <>
          {/* System Health Cards */}
          {statusData && <SystemHealthCards data={statusData} />}

          {/* Alerts Table */}
          {alertsData && (
            <AlertsTable
              alerts={alertsData.alerts}
              total={alertsData.total}
              onAcknowledge={(id) => acknowledgeMutation.mutate(id)}
              onResolve={(id) => resolveMutation.mutate(id)}
              acknowledging={acknowledgeMutation.isPending}
              resolving={resolveMutation.isPending}
            />
          )}

          {/* Webhook Config */}
          {webhookLoading ? (
            <div className="text-sm text-gray-400">Loading webhook config...</div>
          ) : (
            webhookData && (
              <WebhookConfig
                config={webhookData}
                onSave={(url) => webhookMutation.mutate(url)}
                saving={webhookMutation.isPending}
              />
            )
          )}
        </>
      )}
    </div>
  );
}
