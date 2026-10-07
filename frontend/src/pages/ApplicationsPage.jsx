import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, RefreshCw, Plus, ArrowRight, AppWindow, Users, Key } from 'lucide-react';
import { Badge, Spinner, EmptyState, Modal, AlertBanner, ToolLogo, ProgressBar } from '../components/ui';
import { mockApplications } from '../api/mockData';
import { getApplications, createApplication } from '../api/services';
import { formatNumber, capitalize } from '../utils/formatters';

const ApplicationsPage = () => {
  const navigate = useNavigate();
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newApp, setNewApp] = useState({
    application_name: '',
    application_code: '',
    vendor_name: '',
    category: 'Productivity',
    status: 'inactive',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getApplications();
      setApps(res.data);
    } catch (err) {
      console.warn('API error, falling back to mock applications:', err);
      setApps(mockApplications);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = apps.filter((a) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      a.application_name.toLowerCase().includes(q) ||
      a.vendor_name?.toLowerCase().includes(q) ||
      a.category?.toLowerCase().includes(q);
    const matchStatus = filterStatus === 'all' || a.status === filterStatus;
    return matchSearch && matchStatus;
  });

  const activeCount = apps.filter((a) => a.status === 'active').length;
  const inactiveCount = apps.filter((a) => a.status === 'inactive').length;

  const handleTileClick = (appName) => {
    navigate(`/licenses?app=${encodeURIComponent(appName)}`);
  };

  const handleCreateApp = async () => {
    if (!newApp.application_name.trim()) return;
    try {
      const res = await createApplication(newApp);
      setApps((prev) => [...prev, res.data]);
      setSuccess(`Application "${newApp.application_name}" added.`);
    } catch (err) {
      setApps((prev) => [
        ...prev,
        { ...newApp, application_id: `app-${Date.now()}` },
      ]);
      setSuccess(`Application "${newApp.application_name}" registered.`);
    }
    setShowAddModal(false);
    setNewApp({
      application_name: '',
      application_code: '',
      vendor_name: '',
      category: 'Productivity',
      status: 'inactive',
    });
    setTimeout(() => setSuccess(''), 3000);
  };

  if (loading) return <Spinner />;

  return (
    <>
      {success && <AlertBanner type="success" message={success} onDismiss={() => setSuccess('')} />}
      {error && <AlertBanner type="error" message={error} onDismiss={() => setError('')} />}

      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Applications</h1>
          <p className="page-desc">
            {apps.length} configured tools · {activeCount} active · {inactiveCount} inactive
          </p>
        </div>
        <div className="flex gap-8">
          <button id="apps-refresh-btn" className="btn btn-secondary btn-sm" onClick={load}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button
            id="apps-add-btn"
            className="btn btn-primary btn-sm"
            onClick={() => setShowAddModal(true)}
          >
            <Plus size={14} /> Add Application
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="toolbar">
        <div className="input-with-icon" style={{ width: 260 }}>
          <span className="input-icon"><Search size={14} /></span>
          <input
            id="apps-search"
            className="input"
            placeholder="Search applications…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          id="apps-status-filter"
          className="select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">All Statuses ({apps.length})</option>
          <option value="active">Active ({activeCount})</option>
          <option value="inactive">Inactive ({inactiveCount})</option>
        </select>

        <span className="toolbar-spacer" />
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Showing {filtered.length} of {apps.length}
        </span>
      </div>

      {/* Compact Tiles Grid */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<AppWindow size={24} color="var(--gray-400)" />}
          title="No applications found"
          description="Try adjusting your search or filters."
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          {filtered.map((app) => {
            const isActive = app.status === 'active';
            const utilPct = app.total_seats
              ? Math.min(100, Math.round(((app.assigned_seats || 0) / app.total_seats) * 100))
              : 0;

            return (
              <div
                key={app.application_id || app.application_name}
                id={`app-tile-${app.application_code || app.application_name}`}
                className="card app-tile-compact"
                onClick={() => handleTileClick(app.application_name)}
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                  position: 'relative',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  border: isActive
                    ? '1px solid rgba(99, 102, 241, 0.2)'
                    : '1px solid var(--border-color)',
                  background: 'var(--bg-card)',
                  borderRadius: 12,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.borderColor = isActive ? 'var(--primary-400)' : 'var(--gray-300)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '';
                  e.currentTarget.style.transform = '';
                  e.currentTarget.style.borderColor = isActive
                    ? 'rgba(99, 102, 241, 0.2)'
                    : 'var(--border-color)';
                }}
              >
                {/* Top Accent Line */}
                <div
                  style={{
                    height: 3,
                    background: isActive
                      ? 'linear-gradient(90deg, #10B981, #059669)'
                      : 'linear-gradient(90deg, #94a3b8, #cbd5e1)',
                  }}
                />

                <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {/* Header: Logo, Name, Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                      <ToolLogo name={app.application_name} size={34} />
                      <div style={{ minWidth: 0 }}>
                        <div
                          style={{
                            fontWeight: 600,
                            fontSize: 14,
                            color: 'var(--text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                          title={app.application_name}
                        >
                          {app.application_name}
                        </div>
                        <div
                          style={{
                            fontSize: 11,
                            color: 'var(--text-muted)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {app.category || app.vendor_name}
                        </div>
                      </div>
                    </div>

                    <Badge variant={isActive ? 'success' : 'neutral'} dot>
                      {isActive ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>

                  {/* Compact Metrics */}
                  <div
                    style={{
                      background: 'var(--gray-50)',
                      borderRadius: 8,
                      padding: '8px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: 12,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Key size={13} color="var(--gray-500)" />
                      <span style={{ color: 'var(--text-muted)' }}>Licenses:</span>
                      <strong style={{ color: 'var(--text-primary)' }}>{app.licenses_count ?? 0}</strong>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Users size={13} color="var(--gray-500)" />
                      <span style={{ color: 'var(--text-muted)' }}>Assigned:</span>
                      <strong style={{ color: 'var(--text-primary)' }}>
                        {formatNumber(app.assigned_seats || 0)}
                        {isActive && app.total_seats ? ` / ${formatNumber(app.total_seats)}` : ' / 0'}
                      </strong>
                    </div>
                  </div>

                  {/* Progress Bar if active */}
                  {isActive && app.total_seats > 0 && (
                    <div>
                      <div className="flex-between" style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                        <span>Utilization</span>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{utilPct}%</span>
                      </div>
                      <ProgressBar value={utilPct} max={100} />
                    </div>
                  )}

                  {!isActive && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      Integration pending · Ready to sync
                    </div>
                  )}
                </div>

                {/* Footer Link (Clean, no edit option) */}
                <div
                  style={{
                    padding: '8px 16px',
                    borderTop: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: 12,
                    fontWeight: 500,
                    color: isActive ? 'var(--primary-600)' : 'var(--text-secondary)',
                    background: 'var(--bg-card)',
                  }}
                >
                  <span>View Licenses</span>
                  <ArrowRight size={13} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Application Modal (No Edit Option on tiles) */}
      <Modal
        open={showAddModal}
        title="Register Application"
        onClose={() => setShowAddModal(false)}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
              Cancel
            </button>
            <button
              id="app-modal-submit"
              className="btn btn-primary"
              onClick={handleCreateApp}
              disabled={!newApp.application_name.trim()}
            >
              Add Application
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label className="input-label" htmlFor="new-app-name">Application Name *</label>
            <input
              id="new-app-name"
              className="input"
              placeholder="e.g. Asana"
              value={newApp.application_name}
              onChange={(e) => setNewApp((prev) => ({ ...prev, application_name: e.target.value }))}
            />
          </div>
          <div className="grid-2" style={{ gap: 12 }}>
            <div>
              <label className="input-label" htmlFor="new-app-vendor">Vendor</label>
              <input
                id="new-app-vendor"
                className="input"
                placeholder="e.g. Asana Inc."
                value={newApp.vendor_name}
                onChange={(e) => setNewApp((prev) => ({ ...prev, vendor_name: e.target.value }))}
              />
            </div>
            <div>
              <label className="input-label" htmlFor="new-app-cat">Category</label>
              <input
                id="new-app-cat"
                className="input"
                placeholder="e.g. Productivity"
                value={newApp.category}
                onChange={(e) => setNewApp((prev) => ({ ...prev, category: e.target.value }))}
              />
            </div>
          </div>
          <div>
            <label className="input-label" htmlFor="new-app-status">Status</label>
            <select
              id="new-app-status"
              className="select"
              value={newApp.status}
              onChange={(e) => setNewApp((prev) => ({ ...prev, status: e.target.value }))}
              style={{ width: '100%' }}
            >
              <option value="inactive">Inactive</option>
              <option value="active">Active</option>
            </select>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default ApplicationsPage;
