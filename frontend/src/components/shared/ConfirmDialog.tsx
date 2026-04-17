import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  /** If set, user must type this exact string before confirming */
  requireTyping?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  requireTyping,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const [typed, setTyped] = useState('');

  if (!isOpen) return null;

  const canConfirm = !requireTyping || typed === requireTyping;

  const btnClass = {
    danger:  'bg-red-600 hover:bg-red-700 focus:ring-red-500 disabled:bg-red-300',
    warning: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500 disabled:bg-yellow-300',
    info:    'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-300',
  }[variant];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pb-20">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-gray-900 bg-opacity-50" onClick={onCancel} />

        {/* Dialog */}
        <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full p-6">

          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              {variant === 'danger' && (
                <div className="w-9 h-9 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
              )}
              <h3 className="text-base font-bold text-gray-900">{title}</h3>
            </div>
            <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 ml-4">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Message */}
          <p className="text-sm text-gray-600 mb-4 whitespace-pre-line leading-relaxed">{message}</p>

          {/* Type-to-confirm */}
          {requireTyping && (
            <div className="mb-5">
              <label className="block text-xs font-semibold text-gray-500 mb-1.5">
                Type <span className="font-mono text-red-600 bg-red-50 px-1 rounded">{requireTyping}</span> to confirm
              </label>
              <input
                type="text"
                value={typed}
                onChange={(e) => setTyped(e.target.value)}
                placeholder={requireTyping}
                autoFocus
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              {cancelLabel}
            </button>
            <button
              onClick={() => { setTyped(''); onConfirm(); }}
              disabled={!canConfirm}
              className={`px-4 py-2 text-sm font-semibold text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed transition-colors ${btnClass}`}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
