import { useState } from 'react';
import { Webhook, Save, Trash2 } from 'lucide-react';
import type { WebhookConfigResponse } from '../../../lib/api';

interface Props {
  config: WebhookConfigResponse;
  onSave: (url: string | null) => void;
  saving: boolean;
}

export default function WebhookConfig({ config, onSave, saving }: Props) {
  const [url, setUrl] = useState('');
  const [editing, setEditing] = useState(false);

  const handleSave = () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    onSave(trimmed);
    setEditing(false);
    setUrl('');
  };

  const handleRemove = () => {
    onSave(null);
    setEditing(false);
    setUrl('');
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center gap-2 mb-4">
        <Webhook className="h-4 w-4 text-gray-500" />
        <h3 className="text-sm font-bold text-gray-900">Webhook Configuration</h3>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-gray-500 uppercase">Status:</span>
          <span
            className={`inline-block px-2 py-0.5 text-xs font-bold rounded-full ${
              config.configured
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}
          >
            {config.configured ? 'Configured' : 'Not configured'}
          </span>
        </div>

        {config.configured && config.url && (
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-gray-500 uppercase">URL:</span>
            <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-700">
              {config.url}
            </code>
          </div>
        )}

        {editing ? (
          <div className="flex gap-2">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://hooks.example.com/webhook"
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              onClick={handleSave}
              disabled={saving || !url.trim()}
              className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              <Save className="h-3 w-3" />
              Save
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setEditing(true)}
              className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
            >
              {config.configured ? 'Update URL' : 'Set URL'}
            </button>
            {config.configured && (
              <button
                onClick={handleRemove}
                disabled={saving}
                className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold text-red-700 bg-red-50 rounded-lg hover:bg-red-100 disabled:opacity-50 transition-colors"
              >
                <Trash2 className="h-3 w-3" />
                Remove
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
