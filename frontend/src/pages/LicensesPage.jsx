import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search, Plus, RefreshCw, Key, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, ShieldCheck, Cloud, Briefcase,
  Mail, Video, BarChart2, Zap, Code, ShieldAlert, TrendingUp,
  Headphones, Globe, Layers, Database, Bot, Sparkles, Filter,
  Users, UserCheck, X, ExternalLink, Copy, Check,
} from 'lucide-react';
import { Badge, Spinner, EmptyState, ProgressBar, Modal, AlertBanner, ToolLogo } from '../components/ui';
import { mockLicenses } from '../api/mockData';
import { getLicenses, createLicense, triggerSync, getLicenseUsers } from '../api/services';
import {
  formatDate, formatNumber, formatPercent, capitalize, daysUntil, getExpiryUrgency, getUtilizationLevel,
} from '../utils/formatters';

const CATEGORY_ICONS = {
  'Business Suite': ShieldCheck,
  'Productivity & Cloud': Cloud,
  'Enterprise Cloud': Briefcase,
  'Messaging & Email': Mail,
  'Collaboration & Meetings': Video,
  'Analytics & BI': BarChart2,
  'Automation & Workflows': Zap,
  'Developer & Sandbox': Code,
  'Cybersecurity & Identity': ShieldAlert,
  'CRM & Sales': TrendingUp,
  'Customer Service & Support': Headphones,
  'Low-Code Web Apps': Globe,
  'Enterprise ERP': Layers,
  'Cloud ERP': Database,
  'AI & Copilot Studio': Bot,
  'Team Collaboration': Sparkles,
  'Visual Collaboration': Globe,
  'Cloud Storage': Cloud,
  'Video Conferencing': Video,
  'Project Management': Layers,
  'SASE & Security': ShieldAlert,
};

// ── License Users Modal ──────────────────────────────────────────────────────
const LicenseUsersModal = ({ open, license, onClose }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userSearch, setUserSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [copiedEmail, setCopiedEmail] = useState('');

  useEffect(() => {
    if (!license || !open) return;
    let active = true;
    setLoading(true);
    getLicenseUsers(license)
      .then((res) => {
        if (active) setUsers(res.data || []);
      })
      .catch((err) => {
        console.warn('Failed to load license users:', err);
        if (active) setUsers([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [license, open]);

  if (!license) return null;

  const filteredUsers = users.filter((u) => {
    const q = userSearch.toLowerCase();
    const matchesSearch =
      !q ||
      u.name?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q) ||
      u.department?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q);
    const matchesStatus = statusFilter === 'all' || u.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleCopyEmail = (email) => {
    navigator.clipboard?.writeText(email);
    setCopiedEmail(email);
    setTimeout(() => setCopiedEmail(''), 2000);
  };

  const utilPct = license.total_quantity
    ? Math.min(100, Math.round(((license.allocated_quantity || license.used_quantity || 0) / license.total_quantity) * 100))
    : 0;

  return (
    <Modal
      open={open}
      title=""
      onClose={onClose}
      footer={<button className="btn btn-secondary" onClick={onClose}>Close</button>}
    >
      {/* Header Info */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ToolLogo name={license.application_name} size={42} />
          <div>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
              {license.license_name}
            </h3>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              {license.application_name} · <span style={{ fontFamily: 'monospace' }}>{license.raw_sku_part_number || license.product_code || 'SKU'}</span>
            </div>
          </div>
        </div>
        <Badge variant={license.status === 'active' ? 'success' : 'neutral'}>
          {capitalize(license.status)}
        </Badge>
      </div>

      {/* Utilization & Seat Summary */}
      <div
        style={{
          background: 'var(--gray-50)',
          borderRadius: 10,
          padding: '12px 16px',
          border: '1px solid var(--border-color)',
          marginBottom: 16,
        }}
      >
        <div className="flex-between" style={{ marginBottom: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
            Assigned Seats: {formatNumber(license.allocated_quantity || license.used_quantity || 0)} / {formatNumber(license.total_quantity || 0)}
          </span>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
            {utilPct}% Used
          </span>
        </div>
        <ProgressBar value={utilPct} max={100} />
        <div className="flex-between" style={{ marginTop: 6, fontSize: 11, color: 'var(--text-muted)' }}>
          <span>{formatNumber(license.available_quantity || 0)} available seats in pool</span>
          <span>Renewal: {formatDate(license.expiry_date)}</span>
        </div>
      </div>

      {/* Search & Status Filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <div className="input-with-icon" style={{ flex: 1, minWidth: 200 }}>
          <span className="input-icon"><Search size={14} /></span>
          <input
            className="input"
            placeholder="Search assigned users by name, email, department…"
            value={userSearch}
            onChange={(e) => setUserSearch(e.target.value)}
            style={{ height: 34, fontSize: 13 }}
          />
        </div>
        <select
          className="select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ height: 34, fontSize: 13 }}
        >
          <option value="all">All Statuses ({users.length})</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {/* Users Table */}
      {loading ? (
        <div style={{ padding: '30px 0', textAlign: 'center' }}>
          <Spinner size={30} />
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
            Fetching users assigned to this license…
          </div>
        </div>
      ) : filteredUsers.length === 0 ? (
        <EmptyState
          icon={<Users size={22} color="var(--gray-400)" />}
          title="No users found"
          description={userSearch ? 'No assigned users match your search query.' : 'No users currently assigned to this license.'}
        />
      ) : (
        <div style={{ maxHeight: 340, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 8 }}>
          <table className="table" style={{ margin: 0 }}>
            <thead>
              <tr style={{ background: 'var(--gray-50)', position: 'sticky', top: 0, zIndex: 1 }}>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>User</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Department / Role</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Status</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Assigned Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u, idx) => (
                <tr key={u.user_id || u.email || idx}>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div
                        style={{
                          width: 30,
                          height: 30,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, var(--primary-500), var(--primary-700))',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 600,
                          fontSize: 12,
                          flexShrink: 0,
                        }}
                      >
                        {u.name?.charAt(0)?.toUpperCase() || 'U'}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
                          {u.name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.email}</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopyEmail(u.email);
                            }}
                            title="Copy email"
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              padding: 2,
                              color: copiedEmail === u.email ? 'var(--success-600)' : 'var(--gray-400)',
                            }}
                          >
                            {copiedEmail === u.email ? <Check size={11} /> : <Copy size={11} />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontSize: 12, fontWeight: 500 }}>{u.role || 'Member'}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.department || 'General'}</div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <Badge variant={u.status === 'active' ? 'success' : 'neutral'}>
                      {capitalize(u.status || 'active')}
                    </Badge>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: 'var(--text-muted)' }}>
                    {u.assigned_date ? formatDate(u.assigned_date) : 'Active'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
};

// ── Main Licenses Page ────────────────────────────────────────────────────────
const LicensesPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeAppParam = searchParams.get('app') || 'all';

  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterApp, setFilterApp] = useState(activeAppParam);
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState('grouped'); // 'grouped' or 'flat'
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [newLic, setNewLic] = useState({
    license_name: '',
    application_name: 'Microsoft 365',
    vendor: 'Microsoft',
    license_type: 'Business Suite',
    total_quantity: 100,
    used_quantity: 50,
    expiry_date: '2026-12-31',
    billing_frequency: 'annual',
    status: 'active',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Sync param to filter state
  useEffect(() => {
    if (activeAppParam) {
      setFilterApp(activeAppParam);
    }
  }, [activeAppParam]);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getLicenses();
      setLicenses(res.data);
    } catch (err) {
      console.warn('API error, falling back to mock data', err);
      setLicenses(mockLicenses);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSyncAll = async () => {
    setSyncing(true);
    try {
      await triggerSync('ms-graph');
      await load();
      setSuccess('Live Microsoft 365 & Slack licenses synchronized successfully!');
    } catch (err) {
      console.warn('Sync failed:', err);
    } finally {
      setSyncing(false);
      setTimeout(() => setSuccess(''), 3500);
    }
  };

  const handleAddLicense = async () => {
    if (!newLic.license_name.trim()) return;
    try {
      const payload = {
        ...newLic,
        total_quantity: Number(newLic.total_quantity),
        allocated_quantity: Number(newLic.used_quantity),
        used_quantity: Number(newLic.used_quantity),
        available_quantity: Math.max(0, Number(newLic.total_quantity) - Number(newLic.used_quantity)),
      };
      const res = await createLicense(payload);
      setLicenses((prev) => [res.data, ...prev]);
      setSuccess('License added successfully.');
      setShowAddModal(false);
    } catch (err) {
      setLicenses((prev) => [{ ...newLic, license_id: `lic-${Date.now()}` }, ...prev]);
      setSuccess('License added.');
      setShowAddModal(false);
    }
    setTimeout(() => setSuccess(''), 3000);
  };

  // All monitored tools
  const ALL_TOOLS = ['Microsoft 365', 'Slack', 'Lucidchart', 'Box', 'Zoom', 'Sofia - (Pilot)', '_Jira', 'CATO'];
  const appNames = ALL_TOOLS;
  const licenseTypes = [...new Set(licenses.map((l) => l.license_type).filter(Boolean))];

  // Filtering
  const filtered = licenses.filter((l) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      l.license_name.toLowerCase().includes(q) ||
      l.raw_sku_part_number?.toLowerCase().includes(q) ||
      l.product_code?.toLowerCase().includes(q) ||
      l.application_name?.toLowerCase().includes(q) ||
      l.license_type?.toLowerCase().includes(q) ||
      l.vendor?.toLowerCase().includes(q);

    const matchApp =
      filterApp === 'all' ||
      l.application_name?.toLowerCase() === filterApp.toLowerCase();
    const matchType = filterType === 'all' || l.license_type === filterType;
    const matchStatus = filterStatus === 'all' || l.status === filterStatus;
    return matchSearch && matchApp && matchType && matchStatus;
  });

  // Group filtered licenses by application
  const groupedByApp = {};
  const toolsToDisplay =
    filterApp === 'all'
      ? ALL_TOOLS
      : ALL_TOOLS.filter((t) => t.toLowerCase() === filterApp.toLowerCase());

  toolsToDisplay.forEach((appName) => {
    groupedByApp[appName] = [];
  });

  filtered.forEach((lic) => {
    const app = lic.application_name || 'Other';
    if (!groupedByApp[app]) groupedByApp[app] = [];
    groupedByApp[app].push(lic);
  });

  const handleAppTabClick = (appName) => {
    setFilterApp(appName);
    if (appName === 'all') {
      searchParams.delete('app');
    } else {
      searchParams.set('app', appName);
    }
    setSearchParams(searchParams);
  };

  if (loading) return <Spinner />;

  return (
    <>
      {success && <AlertBanner type="success" message={success} onDismiss={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onDismiss={() => setError('')} />}

      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Enterprise Licenses</h1>
          <p className="page-desc">
            {licenses.length} licenses organized across {appNames.length} applications · Click any license to inspect assigned users
          </p>
        </div>
        <div className="flex gap-8">
          <button
            id="licenses-sync-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleSyncAll}
            disabled={syncing}
          >
            <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing...' : 'Sync Active Tools'}
          </button>
          <button
            id="licenses-add-btn"
            className="btn btn-primary btn-sm"
            onClick={() => setShowAddModal(true)}
          >
            <Plus size={14} /> Add License
          </button>
        </div>
      </div>

      {/* Application Quick Tabs */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          marginBottom: 16,
          overflowX: 'auto',
          paddingBottom: 4,
          alignItems: 'center',
        }}
      >
        <button
          className={`btn btn-sm ${filterApp === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => handleAppTabClick('all')}
        >
          All Applications ({licenses.length})
        </button>

        {appNames.map((name) => {
          const isSelected = filterApp.toLowerCase() === name.toLowerCase();
          const count = licenses.filter((l) => l.application_name === name).length;
          return (
            <button
              key={name}
              className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => handleAppTabClick(name)}
              style={{ display: 'flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap' }}
            >
              <ToolLogo name={name} size={15} />
              <span>{name}</span>
              <span
                style={{
                  fontSize: 10,
                  opacity: 0.8,
                  background: isSelected ? 'rgba(255,255,255,0.2)' : 'var(--gray-200)',
                  padding: '1px 5px',
                  borderRadius: 10,
                }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Filter Toolbar */}
      <div className="toolbar">
        <div className="input-with-icon" style={{ width: 280 }}>
          <span className="input-icon"><Search size={14} /></span>
          <input
            id="licenses-search"
            className="input"
            placeholder="Search licenses, SKUs, categories…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          id="licenses-type-filter"
          className="select"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="all">All License Types</option>
          {licenseTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        <select
          id="licenses-status-filter"
          className="select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>

        <div style={{ display: 'flex', gap: 4, background: 'var(--gray-100)', padding: 2, borderRadius: 8 }}>
          <button
            className="btn btn-sm"
            style={{
              padding: '4px 10px',
              fontSize: 12,
              background: viewMode === 'grouped' ? 'white' : 'transparent',
              boxShadow: viewMode === 'grouped' ? 'var(--shadow-sm)' : 'none',
              color: viewMode === 'grouped' ? 'var(--text-primary)' : 'var(--text-muted)',
              border: 'none',
            }}
            onClick={() => setViewMode('grouped')}
          >
            Grouped View
          </button>
          <button
            className="btn btn-sm"
            style={{
              padding: '4px 10px',
              fontSize: 12,
              background: viewMode === 'flat' ? 'white' : 'transparent',
              boxShadow: viewMode === 'flat' ? 'var(--shadow-sm)' : 'none',
              color: viewMode === 'flat' ? 'var(--text-primary)' : 'var(--text-muted)',
              border: 'none',
            }}
            onClick={() => setViewMode('flat')}
          >
            Table View
          </button>
        </div>

        <span className="toolbar-spacer" />
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          {filtered.length} licenses found
        </span>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Key size={24} color="var(--gray-400)" />}
          title="No licenses match criteria"
          description="Try resetting your filters or search query."
        />
      ) : viewMode === 'grouped' ? (
        /* ── GROUPED BY APPLICATION VIEW ── */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {Object.entries(groupedByApp).map(([appName, appLicenses]) => {
            const totalPurchased = appLicenses.reduce((acc, l) => acc + (l.total_quantity || 0), 0);
            const totalAssigned = appLicenses.reduce((acc, l) => acc + (l.allocated_quantity || l.used_quantity || 0), 0);
            const isActive = appLicenses.some((l) => l.status === 'active');

            return (
              <div
                key={appName}
                className="card"
                style={{
                  overflow: 'hidden',
                  border: '1px solid var(--border-color)',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                {/* Application Group Header */}
                <div
                  style={{
                    padding: '14px 20px',
                    background: 'var(--gray-50)',
                    borderBottom: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: 12,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <ToolLogo name={appName} size={30} />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                          {appName}
                        </h2>
                        <Badge variant={isActive ? 'success' : 'neutral'}>
                          {isActive ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {appLicenses.length} {appLicenses.length === 1 ? 'license tier' : 'license tiers'}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Assigned / Total Seats</div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                        {formatNumber(totalAssigned)} <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>/ {formatNumber(totalPurchased)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Licenses Table for this Application */}
                {appLicenses.length === 0 ? (
                  <div style={{ padding: '24px 20px', textAlign: 'center', background: 'var(--bg-card)' }}>
                    <Key size={18} color="var(--gray-400)" style={{ marginBottom: 6 }} />
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>
                      0 active licenses registered for {appName}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      Software integration pending activation · 0 seats assigned
                    </div>
                  </div>
                ) : (
                  <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
                    <table className="table" style={{ margin: 0 }}>
                      <thead>
                        <tr>
                          <th>License / SKU</th>
                          <th>Category</th>
                          <th>Assigned Seats</th>
                          <th>Utilization</th>
                          <th>Expiry Date</th>
                          <th>Status</th>
                          <th style={{ textAlign: 'right' }}>Assigned Users</th>
                        </tr>
                      </thead>
                      <tbody>
                        {appLicenses.map((lic) => {
                          const utilPct = lic.total_quantity
                            ? Math.min(100, Math.round(((lic.allocated_quantity || lic.used_quantity || 0) / lic.total_quantity) * 100))
                            : 0;
                          const utilLevel = getUtilizationLevel(utilPct);
                          const IconComponent = CATEGORY_ICONS[lic.license_type] || Key;

                          return (
                            <tr
                              key={lic.license_id}
                              style={{ cursor: 'pointer' }}
                              onClick={() => setSelectedLicense(lic)}
                              className="license-row-clickable"
                            >
                              <td>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                  <div
                                    style={{
                                      padding: 6,
                                      borderRadius: 6,
                                      background: 'var(--gray-100)',
                                      color: 'var(--text-secondary)',
                                    }}
                                  >
                                    <IconComponent size={15} />
                                  </div>
                                  <div>
                                    <div style={{ fontWeight: 600, color: 'var(--gray-900)' }}>
                                      {lic.license_name}
                                    </div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                      {lic.raw_sku_part_number || lic.product_code || '—'}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--gray-700)' }}>
                                  {lic.license_type || 'Commercial'}
                                </span>
                              </td>
                              <td>
                                <div style={{ fontSize: 12, fontWeight: 600 }}>
                                  {formatNumber(lic.allocated_quantity || lic.used_quantity || 0)}
                                  <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>
                                    {' '}/ {formatNumber(lic.total_quantity || 0)}
                                  </span>
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                  {formatNumber(lic.available_quantity || 0)} available
                                </div>
                              </td>
                              <td style={{ minWidth: 120 }}>
                                <div className="flex-between" style={{ marginBottom: 4 }}>
                                  <span style={{ fontSize: 11, fontWeight: 600 }}>{utilPct}%</span>
                                </div>
                                <ProgressBar value={utilPct} max={100} variant={utilLevel} />
                              </td>
                              <td>
                                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                                  {formatDate(lic.expiry_date)}
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                  {lic.auto_renew ? 'Auto-renews' : 'Manual renewal'}
                                </div>
                              </td>
                              <td>
                                <Badge variant={lic.status === 'active' ? 'success' : 'neutral'}>
                                  {capitalize(lic.status)}
                                </Badge>
                              </td>
                              <td style={{ textAlign: 'right' }}>
                                <button
                                  className="btn btn-secondary btn-sm"
                                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedLicense(lic);
                                  }}
                                >
                                  <Users size={13} />
                                  <span>Show Users</span>
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* ── FLAT TABLE VIEW ── */
        <div className="table-wrapper">
          <table className="table" id="licenses-table">
            <thead>
              <tr>
                <th>License / Product</th>
                <th>Application</th>
                <th>Category / Type</th>
                <th>Assigned Seats</th>
                <th>Utilization</th>
                <th>Expiry Date</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Assigned Users</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((lic) => {
                const utilPct = lic.total_quantity
                  ? Math.min(100, Math.round(((lic.allocated_quantity || lic.used_quantity || 0) / lic.total_quantity) * 100))
                  : 0;
                const utilLevel = getUtilizationLevel(utilPct);
                const IconComponent = CATEGORY_ICONS[lic.license_type] || Key;

                return (
                  <tr
                    key={lic.license_id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedLicense(lic)}
                    id={`license-row-${lic.license_id}`}
                  >
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div
                          style={{
                            padding: 6,
                            borderRadius: 6,
                            background: 'var(--gray-100)',
                            color: 'var(--text-secondary)',
                          }}
                        >
                          <IconComponent size={15} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--gray-900)' }}>{lic.license_name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                            {lic.raw_sku_part_number || lic.product_code}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <ToolLogo name={lic.application_name} size={18} />
                        <span style={{ fontSize: 13, fontWeight: 500 }}>{lic.application_name}</span>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--gray-700)' }}>
                        {lic.license_type}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontSize: 12, fontWeight: 600 }}>
                        {formatNumber(lic.allocated_quantity || lic.used_quantity)}
                        <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>
                          {' '}/ {formatNumber(lic.total_quantity)}
                        </span>
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {formatNumber(lic.available_quantity)} available
                      </div>
                    </td>
                    <td style={{ minWidth: 120 }}>
                      <div className="flex-between" style={{ marginBottom: 4 }}>
                        <span style={{ fontSize: 11, fontWeight: 600 }}>{utilPct}%</span>
                      </div>
                      <ProgressBar value={utilPct} max={100} variant={utilLevel} />
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
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLicense(lic);
                        }}
                      >
                        <Users size={13} />
                        <span>Show Users</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* License Assigned Users Modal */}
      <LicenseUsersModal
        open={!!selectedLicense}
        license={selectedLicense}
        onClose={() => setSelectedLicense(null)}
      />

      {/* Add License Modal (Price / Cost fields completely removed) */}
      <Modal
        open={showAddModal}
        title="Register License"
        onClose={() => setShowAddModal(false)}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleAddLicense}>
              Add License
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label className="label">License / Product Name</label>
            <input
              className="input"
              placeholder="e.g. Zoom Enterprise One"
              value={newLic.license_name}
              onChange={(e) => setNewLic((l) => ({ ...l, license_name: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">Application</label>
            <select
              className="select"
              value={newLic.application_name}
              onChange={(e) =>
                setNewLic((l) => ({
                  ...l,
                  application_name: e.target.value,
                  vendor: e.target.value,
                }))
              }
              style={{ width: '100%' }}
            >
              <option value="Microsoft 365">Microsoft 365</option>
              <option value="Slack">Slack</option>
              <option value="Lucidchart">Lucidchart</option>
              <option value="Box">Box</option>
              <option value="Zoom">Zoom</option>
              <option value="Sofia - (Pilot)">Sofia - (Pilot)</option>
              <option value="_Jira">_Jira</option>
              <option value="CATO">CATO</option>
            </select>
          </div>
          <div>
            <label className="label">Category / Type</label>
            <input
              className="input"
              placeholder="e.g. Productivity & Cloud"
              value={newLic.license_type}
              onChange={(e) => setNewLic((l) => ({ ...l, license_type: e.target.value }))}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label className="label">Purchased Seats</label>
              <input
                type="number"
                className="input"
                value={newLic.total_quantity}
                onChange={(e) => setNewLic((l) => ({ ...l, total_quantity: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Assigned Seats</label>
              <input
                type="number"
                className="input"
                value={newLic.used_quantity}
                onChange={(e) => setNewLic((l) => ({ ...l, used_quantity: e.target.value }))}
              />
            </div>
          </div>
          <div>
            <label className="label">Expiry / Renewal Date</label>
            <input
              type="date"
              className="input"
              value={newLic.expiry_date}
              onChange={(e) => setNewLic((l) => ({ ...l, expiry_date: e.target.value }))}
            />
          </div>
        </div>
      </Modal>
    </>
  );
};

export default LicensesPage;
