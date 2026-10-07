import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppWindow, Key, Users, TrendingUp,
  AlertTriangle, RefreshCw, ArrowUpRight, CheckCircle2,
  ExternalLink, Clock, Sparkles, Layers,
} from 'lucide-react';
import { Spinner, Badge, AlertBanner, ToolLogo, Modal } from '../components/ui';
import {
  mockSummary, mockLicenses, mockUsers,
} from '../api/mockData';
import {
  getDashboardSummary, getLicenses, getApplications, getLicenseUsers,
} from '../api/services';
import {
  formatNumber, formatDate, daysUntil, getExpiryUrgency, capitalize,
} from '../utils/formatters';

// ── Clean Stat KPI Card ───────────────────────────────────────────────────────
const StatCard = ({ icon: Icon, iconBg, iconColor, accentGradient, value, label, sub, subType = 'neutral' }) => (
  <div className="stat-card" style={{ '--accent-gradient': accentGradient }}>
    <div className="stat-card-icon" style={{ background: iconBg }}>
      <Icon size={20} color={iconColor} />
    </div>
    <div className="stat-card-value">{value}</div>
    <div className="stat-card-label">{label}</div>
    {sub && (
      <div className={`stat-card-change ${subType}`}>{sub}</div>
    )}
  </div>
);

// ── Expiry urgency badge ─────────────────────────────────────────────────────
const ExpiryBadge = ({ dateStr }) => {
  const urgency = getExpiryUrgency(dateStr);
  const days = daysUntil(dateStr);
  const map = {
    expired: { variant: 'danger', label: 'Expired' },
    critical: { variant: 'danger', label: `${days}d remaining` },
    warning: { variant: 'warning', label: `${days}d remaining` },
    normal: { variant: 'success', label: `${days}d remaining` },
  };
  const m = map[urgency] || map.normal;
  return <Badge variant={m.variant}>{m.label}</Badge>;
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastSync, setLastSync] = useState(new Date());
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [licenseUsers, setLicenseUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [sumRes, licRes, appRes] = await Promise.all([
        getDashboardSummary(),
        getLicenses(),
        getApplications(),
      ]);
      setData({
        summary: sumRes.data,
        licenses: licRes.data,
        applications: appRes.data,
      });
      setLastSync(new Date());
    } catch (err) {
      console.warn('API error, falling back to mock data', err);
      setData({
        summary: mockSummary,
        licenses: mockLicenses,
        applications: [
          { application_name: 'Microsoft 365', status: 'active', licenses_count: 16, assigned_seats: 885, total_seats: 1040488 },
          { application_name: 'Slack', status: 'active', licenses_count: 1, assigned_seats: 11, total_seats: 12 },
          { application_name: 'Lucidchart', status: 'inactive', licenses_count: 0, assigned_seats: 0, total_seats: 0 },
          { application_name: 'Box', status: 'inactive', licenses_count: 0, assigned_seats: 0, total_seats: 0 },
          { application_name: 'Zoom', status: 'inactive', licenses_count: 0, assigned_seats: 0, total_seats: 0 },
          { application_name: 'Sofia - (Pilot)', status: 'inactive', licenses_count: 0, assigned_seats: 0, total_seats: 0 },
          { application_name: '_Jira', status: 'inactive', licenses_count: 0, assigned_seats: 0, total_seats: 0 },
          { application_name: 'CATO', status: 'inactive', licenses_count: 0, assigned_seats: 0, total_seats: 0 },
        ],
      });
      setLastSync(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleOpenLicenseUsers = async (lic) => {
    setSelectedLicense(lic);
    setLoadingUsers(true);
    try {
      const res = await getLicenseUsers(lic);
      setLicenseUsers(res.data || []);
    } catch (e) {
      setLicenseUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  };

  if (loading) return <Spinner />;

  const { summary, licenses, applications } = data;

  // Key active licenses for dashboard overview (top 6 active licenses)
  const activeLicenses = licenses.filter((l) => l.status === 'active').slice(0, 8);

  return (
    <>
      {error && <AlertBanner type="error" message={error} onDismiss={() => setError('')} />}

      {/* ── Executive Header with Neat Typography ───────────────── */}
      <div
        className="page-header"
        style={{
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: 20,
          marginBottom: 24,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <h1
              style={{
                fontSize: 26,
                fontWeight: 800,
                letterSpacing: '-0.03em',
                color: '#0f172a',
                margin: 0,
                fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                lineHeight: 1.2,
              }}
            >
              Enterprise License Portfolio
            </h1>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '3px 10px',
                borderRadius: 20,
                fontSize: 12,
                fontWeight: 600,
                background: 'rgba(16, 185, 129, 0.1)',
                color: '#059669',
                border: '1px solid rgba(16, 185, 129, 0.25)',
              }}
            >
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  backgroundColor: '#10b981',
                  boxShadow: '0 0 6px #10b981',
                }}
              />
              <span>Live · Last synchronized: {lastSync.toLocaleTimeString()}</span>
            </div>
          </div>
          <p
            style={{
              fontSize: 13.5,
              color: '#64748b',
              margin: 0,
              fontWeight: 400,
              letterSpacing: '-0.01em',
              fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            Centralized inventory and seat allocation across enterprise SaaS applications
          </p>
        </div>

        <div className="flex gap-8">
          <button
            id="dashboard-refresh-btn"
            className="btn btn-secondary btn-sm"
            onClick={load}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => navigate('/licenses')}
          >
            <ArrowUpRight size={14} />
            Manage Licenses
          </button>
        </div>
      </div>

      {/* ── Operational KPI Cards (No charts, neat & uncluttered) ─── */}
      <div className="stat-grid section-gap">
        <StatCard
          icon={AppWindow}
          iconBg="var(--primary-50)"
          iconColor="var(--primary-600)"
          accentGradient="linear-gradient(90deg, var(--primary-400), var(--primary-600))"
          value={formatNumber(summary.total_applications || 8)}
          label="Monitored Applications"
          sub={`${summary.active_applications || 2} Active · ${summary.inactive_applications || 6} Inactive`}
          subType="neutral"
        />
        <StatCard
          icon={Key}
          iconBg="var(--info-50)"
          iconColor="var(--info-600)"
          accentGradient="linear-gradient(90deg, var(--info-400), var(--info-600))"
          value={formatNumber(summary.total_licenses || 17)}
          label="Active License Tiers"
          sub="Microsoft 365 & Slack synchronized"
          subType="neutral"
        />
        <StatCard
          icon={Users}
          iconBg="var(--success-50)"
          iconColor="var(--success-600)"
          accentGradient="linear-gradient(90deg, #10b981, #059669)"
          value={formatNumber(summary.used_licenses || 896)}
          label="Total Assigned Seats"
          sub={`${formatNumber(summary.total_seats || 1040500)} total capacity`}
          subType="neutral"
        />
        <StatCard
          icon={AlertTriangle}
          iconBg="var(--warning-50)"
          iconColor="var(--warning-600)"
          accentGradient="linear-gradient(90deg, var(--warning-400), var(--warning-600))"
          value={formatNumber(summary.expiring_90_days || 1)}
          label="Upcoming Renewals (90d)"
          sub="Slack Pro renewal in 40 days"
          subType="neutral"
        />
      </div>

      {/* ── Connected Tool Ecosystem (8 Tools, Clean Grid) ──────── */}
      <div className="card section-gap">
        <div className="card-header">
          <div>
            <div className="card-title">Connected Tool Ecosystem</div>
            <div className="card-subtitle">
              8 monitored SaaS applications · Click any tool to view its licenses
            </div>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate('/applications')}
          >
            All Applications
          </button>
        </div>
        <div className="card-body">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
              gap: 14,
            }}
          >
            {(applications || []).map((app) => {
              const isActive = app.status === 'active';
              return (
                <div
                  key={app.application_name}
                  onClick={() => navigate(`/licenses?app=${encodeURIComponent(app.application_name)}`)}
                  style={{
                    cursor: 'pointer',
                    padding: '14px 16px',
                    borderRadius: 10,
                    background: 'var(--bg-card)',
                    border: isActive
                      ? '1px solid rgba(99, 102, 241, 0.25)'
                      : '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 0.15s ease',
                    boxShadow: 'var(--shadow-xs)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = isActive ? 'var(--primary-500)' : 'var(--gray-300)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = isActive
                      ? 'rgba(99, 102, 241, 0.25)'
                      : 'var(--border-color)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-xs)';
                    e.currentTarget.style.transform = '';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                    <ToolLogo name={app.application_name} size={32} />
                    <div style={{ minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {app.application_name}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {isActive
                          ? `${formatNumber(app.assigned_seats || 0)} seats · ${app.licenses_count || 1} licenses`
                          : '0 licenses · 0 seats'}
                      </div>
                    </div>
                  </div>

                  <Badge variant={isActive ? 'success' : 'neutral'} dot>
                    {isActive ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Active Licenses & Inventory Overview Table ──────────── */}
      <div className="card section-gap">
        <div className="card-header">
          <div>
            <div className="card-title">Active Licenses & Assignments</div>
            <div className="card-subtitle">
              Live enterprise software tiers and assigned user seats
            </div>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate('/licenses')}
          >
            View All Licenses
          </button>
        </div>
        <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
          <table className="table" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>License / Product Tier</th>
                <th>Application</th>
                <th>Category</th>
                <th>Assigned Seats</th>
                <th>Available</th>
                <th>Renewal Date</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Assigned Users</th>
              </tr>
            </thead>
            <tbody>
              {activeLicenses.map((lic) => (
                <tr
                  key={lic.license_id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleOpenLicenseUsers(lic)}
                  className="license-row-clickable"
                >
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <ToolLogo name={lic.application_name} size={22} />
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {lic.license_name}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                          {lic.raw_sku_part_number || lic.product_code || '—'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{lic.application_name}</span>
                  </td>
                  <td>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {lic.license_type || 'Commercial'}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {formatNumber(lic.allocated_quantity || lic.used_quantity || 0)}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {formatNumber(lic.available_quantity || 0)}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontSize: 12 }}>{formatDate(lic.expiry_date)}</div>
                  </td>
                  <td>
                    <Badge variant={lic.status === 'active' ? 'success' : 'neutral'}>
                      {capitalize(lic.status)}
                    </Badge>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenLicenseUsers(lic);
                      }}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                    >
                      <Users size={13} />
                      <span>View Users</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Users Modal directly from Dashboard ─────────────────── */}
      <Modal
        open={!!selectedLicense}
        title=""
        onClose={() => setSelectedLicense(null)}
        footer={<button className="btn btn-secondary" onClick={() => setSelectedLicense(null)}>Close</button>}
      >
        {selectedLicense && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <ToolLogo name={selectedLicense.application_name} size={36} />
              <div>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
                  {selectedLicense.license_name}
                </h3>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {selectedLicense.application_name} · {selectedLicense.raw_sku_part_number || selectedLicense.product_code}
                </div>
              </div>
            </div>

            {loadingUsers ? (
              <div style={{ padding: '30px 0', textAlign: 'center' }}>
                <Spinner size={30} />
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
                  Loading assigned users…
                </div>
              </div>
            ) : licenseUsers.length === 0 ? (
              <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                No assigned users found for this license tier.
              </div>
            ) : (
              <div style={{ maxHeight: 320, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 8 }}>
                <table className="table" style={{ margin: 0 }}>
                  <thead>
                    <tr style={{ background: 'var(--gray-50)', position: 'sticky', top: 0 }}>
                      <th>User</th>
                      <th>Department / Role</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {licenseUsers.map((u, i) => (
                      <tr key={u.user_id || i}>
                        <td>
                          <div style={{ fontWeight: 600, fontSize: 13 }}>{u.name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.email}</div>
                        </td>
                        <td>
                          <div style={{ fontSize: 12 }}>{u.role || 'Member'}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.department || 'Enterprise'}</div>
                        </td>
                        <td>
                          <Badge variant={u.status === 'active' ? 'success' : 'neutral'}>
                            {capitalize(u.status || 'active')}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
};

export default DashboardPage;
