import toast from 'react-hot-toast';

/**
 * Maps backend error responses to user-friendly messages and displays them as toasts.
 */

const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'Not authorized. Please log in again.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  409: 'This action conflicts with the current state. Please refresh and try again.',
  422: 'Validation failed. Please check your input.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'An unexpected server error occurred. Please try again later.',
  502: 'The server is temporarily unavailable. Please try again later.',
  503: 'The service is currently unavailable. Please try again later.',
};

/**
 * Extract a user-friendly message from an error object.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // ApiError from api.ts includes parsed backend detail
    if ('status' in error && typeof (error as any).status === 'number') {
      const status = (error as any).status as number;
      // If the error message is just "HTTP 500: ..." use our friendly mapping
      if (error.message.startsWith('HTTP ')) {
        return STATUS_MESSAGES[status] || error.message;
      }
      // Otherwise the backend sent a specific detail message - use it
      return error.message;
    }
    // Network errors
    if (error.message === 'Failed to fetch') {
      return 'Unable to connect to the server. Please check your connection.';
    }
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unexpected error occurred.';
}

/**
 * Show an error toast with a user-friendly message extracted from the error.
 */
export function showError(error: unknown, fallback?: string): void {
  const message = fallback || getErrorMessage(error);
  toast.error(message);
}

/**
 * Show a success toast.
 */
export function showSuccess(message: string): void {
  toast.success(message);
}
