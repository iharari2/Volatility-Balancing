import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '../lib/api';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      await authApi.resetPassword(token, newPassword);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err: any) {
      setError(err.message || 'Reset failed — link may have expired');
    } finally {
      setLoading(false);
    }
  };

  const cardStyle: React.CSSProperties = {
    width: 400,
    padding: 32,
    borderRadius: 12,
    background: '#1e293b',
    boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
  };

  if (!token) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
        <div style={cardStyle}>
          <p style={{ color: '#f87171', textAlign: 'center' }}>Invalid reset link.</p>
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Link to="/forgot-password" style={{ color: '#60a5fa', fontSize: 13 }}>Request a new link</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
      <div style={cardStyle}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', textAlign: 'center', marginBottom: 8 }}>
          Set New Password
        </h1>

        {success ? (
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: '#4ade80', fontSize: 14, marginBottom: 8 }}>Password reset successfully!</p>
            <p style={{ color: '#94a3b8', fontSize: 13 }}>Redirecting to sign in…</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: 13, marginBottom: 4 }}>
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                style={{
                  width: '100%', padding: '10px 12px', borderRadius: 6,
                  border: '1px solid #334155', background: '#0f172a',
                  color: '#f1f5f9', fontSize: 14, boxSizing: 'border-box',
                }}
                placeholder="Min 6 characters"
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: 13, marginBottom: 4 }}>
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                style={{
                  width: '100%', padding: '10px 12px', borderRadius: 6,
                  border: '1px solid #334155', background: '#0f172a',
                  color: '#f1f5f9', fontSize: 14, boxSizing: 'border-box',
                }}
                placeholder="Repeat password"
              />
            </div>

            {error && (
              <div style={{ color: '#f87171', fontSize: 13, marginBottom: 16,
                padding: '8px 12px', background: 'rgba(248,113,113,0.1)', borderRadius: 6 }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '10px 0', borderRadius: 6, border: 'none',
                background: loading ? '#475569' : '#3b82f6', color: '#fff',
                fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Saving…' : 'Set Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
