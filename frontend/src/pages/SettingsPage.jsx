import React, { useState, useEffect } from 'react';
import { Settings, Database, Shield, Bell, Link, CheckCircle, XCircle, HardDrive } from 'lucide-react';
import { getHealth } from '../api/services';

const SettingsPage = () => {
  const [dbHealth, setDbHealth] = useState({ loading: true, live: false, data: null });

  useEffect(() => {
    getHealth()
      .then((res) => setDbHealth({ loading: false, live: true, data: res.data }))
      .catch(() => setDbHealth({ loading: false, live: false, data: null }));
  }, []);

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-desc">Configure your License Management Portal</p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 720 }}>
        {/* Database Status */}
        <div className="card">
          <div className="card-header">
            <div className="flex gap-8" style={{ alignItems: 'center' }}>
              <HardDrive size={16} color="var(--primary-600)" />
              <div className="card-title">Database Storage & Engine</div>
            </div>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                fontSize: 12,
                fontWeight: 600,
                color: dbHealth.live ? '#16a34a' : '#dc2626',
              }}
            >
              {dbHealth.live ? <CheckCircle size={14} /> : <XCircle size={14} />}
              {dbHealth.live ? 'Connected' : 'Offline / Standalone'}
            </span>
          </div>
          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <div style={{ padding: 12, background: 'var(--gray-50)', borderRadius: 8, border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Storage Engine</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>
                  {dbHealth.data?.engine ? `${dbHealth.data.engine.toUpperCase()} (PostgreSQL Compatible)` : 'SQLite / Mock PostgreSQL'}
                </div>
              </div>
              <div style={{ padding: 12, background: 'var(--gray-50)', borderRadius: 8, border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Database File</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>license_portal.db</div>
              </div>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Connected to backend SQLite storage at <code>license_portal.db</code> via FastAPI on port 8000. To use a real PostgreSQL database, set <code>DATABASE_URL=postgresql://...</code> in <code>.env</code>.
            </p>
          </div>
        </div>

        {/* API Configuration */}
        <div className="card">
          <div className="card-header">
            <div className="flex gap-8" style={{ alignItems: 'center' }}>
              <Link size={16} color="var(--primary-600)" />
              <div className="card-title">API Configuration</div>
            </div>
          </div>
          <div className="card-body">
            <div className="input-group" style={{ marginBottom: 14 }}>
              <label className="input-label" htmlFor="api-base-url">Backend API Base URL</label>
              <input
                id="api-base-url"
                className="input"
                defaultValue={import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}
                readOnly
              />
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Proxied by Vite dev server to <code>http://127.0.0.1:8000/api/v1</code>.
            </p>
          </div>
        </div>

      {/* Auth */}
      <div className="card">
        <div className="card-header">
          <div className="flex gap-8" style={{ alignItems: 'center' }}>
            <Shield size={16} color="var(--primary-600)" />
            <div className="card-title">Authentication</div>
          </div>
        </div>
        <div className="card-body">
          <div className="input-group" style={{ marginBottom: 14 }}>
            <label className="input-label" htmlFor="entra-tenant">Microsoft Entra Tenant ID</label>
            <input id="entra-tenant" className="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="entra-client">Client ID</label>
            <input id="entra-client" className="input" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 10 }}>
            Configure Microsoft Entra ID settings. Credentials are stored securely via environment variables on the backend.
          </p>
        </div>
      </div>

      {/* Sync */}
      <div className="card">
        <div className="card-header">
          <div className="flex gap-8" style={{ alignItems: 'center' }}>
            <Database size={16} color="var(--primary-600)" />
            <div className="card-title">Sync Configuration</div>
          </div>
        </div>
        <div className="card-body">
          <div className="input-group" style={{ marginBottom: 14 }}>
            <label className="input-label" htmlFor="sync-frequency">Default Sync Frequency</label>
            <select id="sync-frequency" className="select" style={{ width: '100%' }}>
              <option value="hourly">Every hour</option>
              <option value="6h">Every 6 hours</option>
              <option value="daily" defaultChecked>Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Frequency can be overridden per connector.
          </p>
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <div className="card-header">
          <div className="flex gap-8" style={{ alignItems: 'center' }}>
            <Bell size={16} color="var(--primary-600)" />
            <div className="card-title">Alert Thresholds</div>
          </div>
        </div>
        <div className="card-body">
          <div className="grid-2" style={{ gap: 14 }}>
            <div className="input-group">
              <label className="input-label" htmlFor="expiry-alert-days">Expiry Alert (days before)</label>
              <input id="expiry-alert-days" type="number" className="input" defaultValue={30} min={1} max={365} />
            </div>
            <div className="input-group">
              <label className="input-label" htmlFor="utilization-alert">Utilization Alert (%)</label>
              <input id="utilization-alert" type="number" className="input" defaultValue={90} min={1} max={100} />
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
        <button className="btn btn-secondary">Reset to defaults</button>
        <button id="settings-save-btn" className="btn btn-primary">Save Settings</button>
      </div>
    </div>
  </>
);
};

export default SettingsPage;
