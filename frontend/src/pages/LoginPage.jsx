import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AlertBanner } from '../components/ui';

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      setError('Please enter your email and password.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await new Promise((r) => setTimeout(r, 800)); // simulate latency
      login({ username: form.email.split('@')[0], email: form.email });
      navigate('/');
    } catch {
      setError('Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">LM</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>LicenseHub</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Management Portal</div>
          </div>
        </div>

        <h1 className="login-title">Welcome back</h1>
        <p className="login-subtitle" style={{ marginBottom: 24 }}>
          Sign in to manage your software licenses.
        </p>

        {error && <AlertBanner type="error" message={error} onDismiss={() => setError('')} />}

        <form className="login-form" onSubmit={handleSubmit} id="login-form">
          <div className="input-group">
            <label className="input-label" htmlFor="email">Email address</label>
            <div className="input-with-icon">
              <span className="input-icon"><Mail size={15} /></span>
              <input
                id="email"
                type="email"
                className="input"
                placeholder="admin@company.com"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                autoComplete="email"
                autoFocus
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">Password</label>
            <div className="input-with-icon">
              <span className="input-icon"><Lock size={15} /></span>
              <input
                id="password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                autoComplete="current-password"
              />
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ marginTop: 4 }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                Signing in…
              </>
            ) : (
              <>
                Sign In
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <div className="login-divider" style={{ marginTop: 20 }}>or continue with SSO</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
          {/* Office 365 SSO */}
          <button
            id="office365-login-btn"
            type="button"
            className="btn btn-secondary"
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              padding: '10px 16px',
              border: '1px solid var(--border-color)',
              fontWeight: 500,
            }}
            onClick={() => {
              login({
                username: 'Office 365 Admin',
                email: 'admin@licenseportal.onmicrosoft.com',
                provider: 'Office 365',
                role: 'Global Admin',
                avatar: 'O365',
              });
              navigate('/');
            }}
          >
            <svg width="18" height="18" viewBox="0 0 21 21" fill="none">
              <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
              <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
              <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
              <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
            </svg>
            <span>Sign in with Office 365</span>
          </button>
        </div>

        <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 18 }}>
          Enterprise SAML 2.0 / OpenID Connect Single Sign-On
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
