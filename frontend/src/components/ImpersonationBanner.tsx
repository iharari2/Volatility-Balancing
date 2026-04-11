import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Fixed top banner shown on every page while an admin is impersonating a user.
 * Rendered inside ProtectedRoute so it sits above all page-level layouts.
 */
export default function ImpersonationBanner() {
  const { impersonating, exitImpersonation } = useAuth();
  const navigate = useNavigate();

  if (!impersonating) return null;

  return (
    <div
      style={{ zIndex: 9999 }}
      className="fixed top-0 left-0 right-0 bg-amber-400 text-amber-900 flex items-center justify-between px-5 py-1.5 text-xs font-semibold shadow-md"
    >
      <span>
        👁️ Viewing as{' '}
        <strong>{impersonating.display_name || impersonating.email}</strong>{' '}
        ({impersonating.email}) — {impersonating.role}
      </span>
      <button
        onClick={() => { exitImpersonation(); navigate('/admin/users'); }}
        className="bg-amber-900 text-amber-100 px-3 py-0.5 rounded hover:bg-amber-800 transition-colors"
      >
        ← Return to admin
      </button>
    </div>
  );
}
