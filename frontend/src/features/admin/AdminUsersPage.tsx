import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, AdminUser } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Navigate, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const ROLES = ['owner', 'member'];

export default function AdminUsersPage() {
  const { user, startImpersonation } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [pendingRole, setPendingRole] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [impersonatingId, setImpersonatingId] = useState<string | null>(null);

  const handleViewAs = async (u: AdminUser) => {
    setImpersonatingId(u.id);
    try {
      const res = await adminApi.impersonateUser(u.id);
      startImpersonation(res.token, { ...res.user, tenant_id: res.user.tenant_id });
      navigate('/');
    } catch (err: any) {
      toast.error(err.message || 'Failed to switch user');
    } finally {
      setImpersonatingId(null);
    }
  };

  // Guard: only owners can access
  if (user?.role !== 'owner') {
    return <Navigate to="/" replace />;
  }

  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.listUsers(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: { role?: string; is_active?: boolean } }) =>
      adminApi.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setEditingId(null);
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Update failed');
    },
  });

  const handleRoleEdit = (u: AdminUser) => {
    setEditingId(u.id);
    setPendingRole(u.role);
    setError(null);
  };

  const handleRoleSave = (userId: string) => {
    updateMutation.mutate({ userId, data: { role: pendingRole } });
  };

  const handleToggleActive = (u: AdminUser) => {
    updateMutation.mutate({ userId: u.id, data: { is_active: !u.is_active } });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">Loading users...</div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="text-sm text-gray-500 mt-1">
          Manage users in your tenant. You cannot modify your own account here.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-700">User</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Role</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Status</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Joined</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(users ?? []).map((u) => {
              const isSelf = u.id === user?.id;
              const isEditing = editingId === u.id;
              return (
                <tr key={u.id} className={isSelf ? 'bg-primary-50' : ''}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {u.display_name}
                      {isSelf && (
                        <span className="ml-2 text-[10px] font-bold text-primary-600 bg-primary-100 px-1.5 py-0.5 rounded uppercase">
                          You
                        </span>
                      )}
                    </div>
                    <div className="text-gray-400 text-xs">{u.email}</div>
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <div className="flex items-center gap-2">
                        <select
                          value={pendingRole}
                          onChange={(e) => setPendingRole(e.target.value)}
                          className="border border-gray-300 rounded px-2 py-1 text-sm"
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={() => handleRoleSave(u.id)}
                          disabled={updateMutation.isPending}
                          className="text-xs px-2 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="text-xs px-2 py-1 text-gray-500 hover:text-gray-700"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-700 capitalize">
                        {u.role}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                        u.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-600'
                      }`}
                    >
                      {u.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {!isSelf && !isEditing && (
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => handleViewAs(u)}
                          disabled={impersonatingId === u.id}
                          className="text-xs text-amber-600 hover:text-amber-800 font-medium disabled:opacity-50"
                          title="Switch to this user's view"
                        >
                          {impersonatingId === u.id ? '…' : '👁️ View as'}
                        </button>
                        <button
                          onClick={() => handleRoleEdit(u)}
                          className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        >
                          Edit role
                        </button>
                        <button
                          onClick={() => handleToggleActive(u)}
                          disabled={updateMutation.isPending}
                          className="text-xs text-gray-500 hover:text-red-600 font-medium disabled:opacity-50"
                        >
                          {u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {(users ?? []).length === 0 && (
          <div className="text-center py-12 text-gray-400">No users found.</div>
        )}
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-xl border border-gray-200 text-sm text-gray-600">
        <strong>Roles:</strong>
        <ul className="mt-2 space-y-1 ml-4 list-disc">
          <li>
            <strong>owner</strong> — full access including user management
          </li>
          <li>
            <strong>member</strong> — view positions, monitor trades, see analytics; cannot manage users
          </li>
        </ul>
        <p className="mt-3 text-xs text-gray-400">
          To reset a password, use: <code className="bg-gray-100 px-1 rounded">python scripts/reset_password.py reset --email user@example.com --password newpass</code>
        </p>
      </div>
    </div>
  );
}
