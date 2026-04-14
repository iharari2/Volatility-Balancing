import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTenantPortfolio } from '../contexts/TenantPortfolioContext';
import { portfolioApi, getAuthHeaders } from '../lib/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

type Step = 'welcome' | 'portfolio' | 'position' | 'done';

const TEMPLATES = [
  { id: 'default',      label: 'Standard',     description: '±3% trigger, 20–60% stock allocation' },
  { id: 'conservative', label: 'Conservative',  description: '±5% trigger, 20–40% stock allocation' },
  { id: 'aggressive',   label: 'Aggressive',    description: '±2% trigger, 40–80% stock allocation' },
];

export default function OnboardingPage() {
  const { user } = useAuth();
  const { refreshPortfolios } = useTenantPortfolio();
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>('welcome');
  const [portfolioName, setPortfolioName] = useState('');
  const [template, setTemplate] = useState('default');
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [cash, setCash] = useState('10000');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [createdPortfolioId, setCreatedPortfolioId] = useState('');

  const displayName = user?.display_name || user?.email?.split('@')[0] || 'there';
  const tenantId = user?.tenant_id || 'default';

  // ── Step handlers ────────────────────────────────────────────────────────

  const handleCreatePortfolio = async () => {
    if (!portfolioName.trim()) { setError('Please enter a portfolio name'); return; }
    setError('');
    setBusy(true);
    try {
      const p = await portfolioApi.create(tenantId, {
        name: portfolioName.trim(),
        description: '',
        template,
        hours_policy: 'OPEN_ONLY',
      });
      setCreatedPortfolioId(p.portfolio_id);
      await refreshPortfolios();
      setStep('position');
    } catch (err: any) {
      setError(err.message || 'Failed to create portfolio');
    } finally {
      setBusy(false);
    }
  };

  const handleAddPosition = async () => {
    if (!ticker.trim()) { setError('Please enter a ticker symbol'); return; }
    setError('');
    setBusy(true);
    try {
      await fetch(`${API_BASE}/v1/tenants/${tenantId}/portfolios/${createdPortfolioId}/positions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({
          ticker: ticker.toUpperCase().trim(),
          quantity: parseFloat(shares) || 0,
          cash: parseFloat(cash) || 10000,
        }),
      }).then(r => {
        if (!r.ok) return r.json().then(d => Promise.reject(new Error(d.detail || 'Failed')));
      });
      setStep('done');
    } catch (err: any) {
      setError(err.message || 'Failed to add position');
    } finally {
      setBusy(false);
    }
  };

  const handleSkipPosition = () => setStep('done');

  const handleFinish = () => navigate('/');

  // ── Styles ────────────────────────────────────────────────────────────────

  const wrap: React.CSSProperties = {
    minHeight: '100vh', background: '#0f172a',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '24px',
  };
  const card: React.CSSProperties = {
    width: '100%', maxWidth: 520, background: '#1e293b',
    borderRadius: 16, padding: 40, boxShadow: '0 8px 40px rgba(0,0,0,0.4)',
  };
  const h1: React.CSSProperties = { color: '#f1f5f9', fontSize: 26, fontWeight: 800, marginBottom: 8 };
  const sub: React.CSSProperties = { color: '#94a3b8', fontSize: 15, marginBottom: 32, lineHeight: 1.5 };
  const label: React.CSSProperties = { display: 'block', color: '#cbd5e1', fontSize: 13, marginBottom: 6 };
  const input: React.CSSProperties = {
    width: '100%', padding: '10px 12px', borderRadius: 8,
    border: '1px solid #334155', background: '#0f172a',
    color: '#f1f5f9', fontSize: 14, boxSizing: 'border-box', marginBottom: 16,
  };
  const btnPrimary: React.CSSProperties = {
    width: '100%', padding: '12px 0', borderRadius: 8, border: 'none',
    background: busy ? '#475569' : '#3b82f6', color: '#fff',
    fontSize: 15, fontWeight: 700, cursor: busy ? 'not-allowed' : 'pointer', marginBottom: 10,
  };
  const btnGhost: React.CSSProperties = {
    width: '100%', padding: '10px 0', borderRadius: 8,
    border: '1px solid #334155', background: 'transparent',
    color: '#94a3b8', fontSize: 14, cursor: 'pointer',
  };
  const errorBox: React.CSSProperties = {
    color: '#f87171', fontSize: 13, marginBottom: 16,
    padding: '8px 12px', background: 'rgba(248,113,113,0.1)', borderRadius: 6,
  };
  const stepDots = (current: number) => (
    <div style={{ display: 'flex', gap: 6, marginBottom: 32 }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: i <= current ? 24 : 8, height: 8, borderRadius: 4,
          background: i <= current ? '#3b82f6' : '#334155',
          transition: 'all 0.2s',
        }} />
      ))}
    </div>
  );

  // ── Render steps ─────────────────────────────────────────────────────────

  if (step === 'welcome') return (
    <div style={wrap}><div style={card}>
      {stepDots(0)}
      <h1 style={h1}>Welcome, {displayName}! 👋</h1>
      <p style={sub}>
        Volatility Balancing is an automated trading robot that buys when prices dip
        and sells when they rise — keeping your portfolio balanced within your chosen guardrails.
        Let's get you set up in two quick steps.
      </p>
      <button style={btnPrimary} onClick={() => setStep('portfolio')}>
        Get Started →
      </button>
    </div></div>
  );

  if (step === 'portfolio') return (
    <div style={wrap}><div style={card}>
      {stepDots(1)}
      <h1 style={h1}>Create your portfolio</h1>
      <p style={sub}>Give it a name and choose a strategy template. You can adjust all parameters later.</p>

      <label style={label}>Portfolio Name</label>
      <input
        style={input} type="text"
        value={portfolioName}
        onChange={e => setPortfolioName(e.target.value)}
        placeholder="e.g. My AAPL Portfolio"
        autoFocus
      />

      <label style={{ ...label, marginBottom: 10 }}>Strategy Template</label>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
        {TEMPLATES.map(t => (
          <label key={t.id} style={{
            display: 'flex', alignItems: 'flex-start', gap: 12, cursor: 'pointer',
            padding: '12px 14px', borderRadius: 8,
            border: `1px solid ${template === t.id ? '#3b82f6' : '#334155'}`,
            background: template === t.id ? 'rgba(59,130,246,0.08)' : 'transparent',
          }}>
            <input
              type="radio" name="template" value={t.id}
              checked={template === t.id}
              onChange={() => setTemplate(t.id)}
              style={{ marginTop: 2, accentColor: '#3b82f6' }}
            />
            <div>
              <div style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 600 }}>{t.label}</div>
              <div style={{ color: '#94a3b8', fontSize: 12 }}>{t.description}</div>
            </div>
          </label>
        ))}
      </div>

      {error && <div style={errorBox}>{error}</div>}
      <button style={btnPrimary} disabled={busy} onClick={handleCreatePortfolio}>
        {busy ? 'Creating…' : 'Create Portfolio →'}
      </button>
    </div></div>
  );

  if (step === 'position') return (
    <div style={wrap}><div style={card}>
      {stepDots(2)}
      <h1 style={h1}>Add your first position</h1>
      <p style={sub}>Tell the robot which stock to trade and how much capital to start with.</p>

      <label style={label}>Stock Ticker</label>
      <input
        style={input} type="text"
        value={ticker}
        onChange={e => setTicker(e.target.value.toUpperCase())}
        placeholder="e.g. AAPL"
        autoFocus
      />

      <label style={label}>Shares Already Owned (0 if starting fresh)</label>
      <input
        style={input} type="number"
        value={shares}
        onChange={e => setShares(e.target.value)}
        placeholder="0"
        min="0"
        step="0.01"
      />

      <label style={label}>Starting Cash ($)</label>
      <input
        style={input} type="number"
        value={cash}
        onChange={e => setCash(e.target.value)}
        placeholder="10000"
        min="0"
        step="100"
      />

      {error && <div style={errorBox}>{error}</div>}
      <button style={btnPrimary} disabled={busy} onClick={handleAddPosition}>
        {busy ? 'Adding…' : 'Add Position →'}
      </button>
      <button style={btnGhost} onClick={handleSkipPosition}>
        Skip for now — I'll add it later
      </button>
    </div></div>
  );

  // done
  return (
    <div style={wrap}><div style={{ ...card, textAlign: 'center' }}>
      <div style={{ fontSize: 56, marginBottom: 16 }}>🎉</div>
      <h1 style={h1}>You're all set!</h1>
      <p style={sub}>
        Your portfolio is ready. The trading robot will start monitoring prices
        and automatically rebalance within your guardrails.
      </p>
      <button style={btnPrimary} onClick={handleFinish}>
        Go to Dashboard →
      </button>
    </div></div>
  );
}
