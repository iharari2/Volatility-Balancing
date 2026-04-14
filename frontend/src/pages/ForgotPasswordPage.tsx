import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../lib/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSubmitted(true);
    } catch (err: any) {
      setError(err.message || 'Request failed');
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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
      <div style={cardStyle}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', textAlign: 'center', marginBottom: 8 }}>
          Reset Password
        </h1>

        {submitted ? (
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 24 }}>
              If that email is registered, a reset link has been sent. Check your inbox.
            </p>
            <Link to="/login" style={{ color: '#60a5fa', fontSize: 13 }}>
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <p style={{ color: '#94a3b8', textAlign: 'center', marginBottom: 24, fontSize: 14 }}>
              Enter your email and we'll send you a reset link.
            </p>
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', color: '#cbd5e1', fontSize: 13, marginBottom: 4 }}>
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 6,
                    border: '1px solid #334155', background: '#0f172a',
                    color: '#f1f5f9', fontSize: 14, boxSizing: 'border-box',
                  }}
                  placeholder="you@example.com"
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
                {loading ? 'Sending…' : 'Send Reset Link'}
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Link to="/login" style={{ color: '#60a5fa', fontSize: 13 }}>
                Back to sign in
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
