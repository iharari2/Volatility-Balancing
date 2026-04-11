const _VITE_BASE = import.meta.env.VITE_API_BASE_URL as string | undefined;
const API_BASE_URL = _VITE_BASE || '';

/**
 * Fetch an Excel file from the backend and trigger a browser download.
 */
export async function exportToExcel(url: string, filename: string): Promise<void> {
  const fullUrl = `${API_BASE_URL}${url}`;
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = { Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const response = await fetch(fullUrl, { headers });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Export failed (HTTP ${response.status})`);
  }

  const blob = await response.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(downloadUrl);
}
