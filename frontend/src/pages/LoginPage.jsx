import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AlertBanner } from '../components/ui';

const LoginPage = () => {
  const { login, isAuthenticated, authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const redirectAfterLogin = location.state?.from?.pathname || '/';

  useEffect(() => {
    if (isAuthenticated) navigate(redirectAfterLogin, { replace: true });
  }, [isAuthenticated, navigate, redirectAfterLogin]);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(username, password);
    } catch (loginError) {
      setError(
        loginError.response?.data?.detail
          || 'Unable to sign in. Check your credentials and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">LM</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>LicenseHub</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Management Portal</div>
          </div>
        </div>

        <h1 className="login-title">Welcome back</h1>
        <p className="login-subtitle" style={{ marginBottom: 24 }}>
          Sign in to access the LicenseHub management portal.
        </p>

        {authError && <AlertBanner type="warning" message={authError} />}
        {error && <AlertBanner type="error" message={error} onDismiss={() => setError('')} />}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label className="input-label" htmlFor="login-username">Username</label>
            <input
              id="login-username"
              className="input"
              type="text"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              maxLength={255}
              disabled={loading}
            />
          </div>
          <div>
            <label className="input-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              className="input"
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              maxLength={1024}
              disabled={loading}
            />
          </div>
          <button
            id="shared-login-btn"
            type="submit"
            className="btn btn-primary"
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
            disabled={loading || !username || !password}
          >
            <span>{loading ? 'Signing in…' : 'Sign in'}</span>
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 18 }}>
          Development shared account. The test form records the selected employee separately from the shared requester.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
