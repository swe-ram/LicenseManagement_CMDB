import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  AppWindow,
  Key,
  Users,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Bell,
  Search,
  LogOut,
  Settings,
  HelpCircle,
  Database,
  CheckCircle,
  AlertTriangle,
  Info,
  ArrowRight,
  X,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { getHealth } from '../../api/services';
import { ToolLogo, Modal, Badge } from '../ui';

const navItems = [
  {
    section: 'Overview',
    items: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
    ],
  },
  {
    section: 'Management',
    items: [
      { to: '/applications', label: 'Applications', icon: AppWindow },
      { to: '/licenses', label: 'Licenses', icon: Key },
    ],
  },
  {
    section: 'Operations',
    items: [
      { to: '/sync', label: 'Sync Jobs', icon: RefreshCw, badge: null },
    ],
  },
];

export const Sidebar = ({ collapsed, onToggle }) => {
  return (
    <nav className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Brand */}
      <NavLink to="/" className="sidebar-brand" style={{ textDecoration: 'none' }}>
        <div className="sidebar-brand-icon">LM</div>
        {!collapsed && (
          <div>
            <div className="sidebar-brand-text">LicenseHub</div>
            <div className="sidebar-brand-sub">Management Portal</div>
          </div>
        )}
      </NavLink>

      {/* Navigation */}
      <div className="sidebar-nav">
        {navItems.map(({ section, items }) => (
          <div key={section} style={{ marginBottom: 16 }}>
            {!collapsed && (
              <div className="sidebar-section-label">{section}</div>
            )}
            {items.map(({ to, label, icon: Icon, badge, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `sidebar-item ${isActive ? 'active' : ''}`
                }
              >
                <span className="sidebar-item-icon">
                  <Icon size={16} />
                </span>
                {!collapsed && (
                  <>
                    <span className="sidebar-item-label">{label}</span>
                    {badge != null && (
                      <span className="sidebar-badge">{badge}</span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        {!collapsed && (
          <NavLink
            to="/settings"
            className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
            style={{ marginBottom: 4 }}
          >
            <span className="sidebar-item-icon"><Settings size={16} /></span>
            <span className="sidebar-item-label">Settings</span>
          </NavLink>
        )}
        <button className="sidebar-collapse-btn" onClick={onToggle} aria-label="Toggle sidebar">
          <span className="sidebar-item-icon">
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </span>
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </nav>
  );
};

export const Topbar = ({ collapsed, title, subtitle }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(true);
  const [dbStatus, setDbStatus] = useState({ connected: false, loading: true, info: null });

  const notifications = [
    {
      id: 1,
      title: 'Slack Pro Renewal Notice',
      message: 'Workspace license renewal scheduled in 40 days (11 allocated seats).',
      time: '1 hour ago',
      type: 'warning',
    },
    {
      id: 2,
      title: 'Microsoft 365 Sync Healthy',
      message: 'Microsoft Graph API synchronized 16 license tiers successfully.',
      time: '2 hours ago',
      type: 'success',
    },
    {
      id: 3,
      title: 'Database Live',
      message: 'Central inventory database connected and operational.',
      time: '4 hours ago',
      type: 'info',
    },
    {
      id: 4,
      title: 'New Applications Ready',
      message: '6 enterprise tools registered (Lucidchart, Box, Zoom, Sofia, Jira, CATO).',
      time: '1 day ago',
      type: 'info',
    },
  ];

  const searchableItems = [
    { type: 'Application', title: 'Microsoft 365', subtitle: 'Productivity Suite · Active', path: '/licenses?app=Microsoft%20365' },
    { type: 'Application', title: 'Slack', subtitle: 'Communication · Active', path: '/licenses?app=Slack' },
    { type: 'Application', title: 'Lucidchart', subtitle: 'Visual Collaboration · Inactive', path: '/licenses?app=Lucidchart' },
    { type: 'Application', title: 'Box', subtitle: 'Cloud Storage · Inactive', path: '/licenses?app=Box' },
    { type: 'Application', title: 'Zoom', subtitle: 'Video Conferencing · Inactive', path: '/licenses?app=Zoom' },
    { type: 'Application', title: 'Sofia - (Pilot)', subtitle: 'AI Assistant · Inactive', path: '/licenses?app=Sofia%20-%20(Pilot)' },
    { type: 'Application', title: '_Jira', subtitle: 'Project Management · Inactive', path: '/licenses?app=_Jira' },
    { type: 'Application', title: 'CATO', subtitle: 'SASE & Security · Inactive', path: '/licenses?app=CATO' },
    { type: 'License', title: 'Microsoft 365 Business Premium', subtitle: 'SKU: O365_BUSINESS_PREMIUM', path: '/licenses?app=Microsoft%20365' },
    { type: 'License', title: 'Microsoft 365 Business Basic', subtitle: 'SKU: O365_BUSINESS_ESSENTIALS', path: '/licenses?app=Microsoft%20365' },
    { type: 'License', title: 'Office 365 E3 Enterprise', subtitle: 'SKU: ENTERPRISEPACK', path: '/licenses?app=Microsoft%20365' },
    { type: 'License', title: 'Slack Pro', subtitle: 'SKU: SLACK_PRO', path: '/licenses?app=Slack' },
    { type: 'Page', title: 'Enterprise Dashboard', subtitle: 'Portfolio Overview & Status', path: '/' },
    { type: 'Page', title: 'Applications Directory', subtitle: 'Manage Registered SaaS Tools', path: '/applications' },
    { type: 'Page', title: 'Licenses Management', subtitle: 'Grouped Licenses & Assigned Users', path: '/licenses' },
    { type: 'Page', title: 'Sync Jobs', subtitle: 'Connector Status & Logs', path: '/sync' },
    { type: 'Page', title: 'Settings', subtitle: 'Account & Integrations Settings', path: '/settings' },
  ];

  const filteredSearchResults = searchableItems.filter((item) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      item.title.toLowerCase().includes(q) ||
      item.subtitle.toLowerCase().includes(q) ||
      item.type.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    let mounted = true;
    const checkStatus = () => {
      getHealth()
        .then((res) => {
          if (mounted) setDbStatus({ connected: true, loading: false, info: res.data });
        })
        .catch(() => {
          if (mounted) setDbStatus({ connected: false, loading: false, info: null });
        });
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <>
      <header className={`topbar ${collapsed ? 'sidebar-collapsed' : ''}`}>
        {/* Title */}
        <div style={{ flex: 1 }}>
          <div className="topbar-title">{title}</div>
          {subtitle && <div className="topbar-subtitle">{subtitle}</div>}
        </div>

        {/* Database Connection Status Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 10px',
            borderRadius: 20,
            fontSize: 12,
            fontWeight: 500,
            background: dbStatus.connected ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: dbStatus.connected ? '#16a34a' : '#dc2626',
            border: `1px solid ${dbStatus.connected ? 'rgba(34, 197, 94, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
          }}
          title={dbStatus.connected ? `Connected to Database (${dbStatus.info?.engine || 'SQLite'} - ${dbStatus.info?.applications_count || 0} apps in DB)` : 'Backend database unreachable (showing fallback data)'}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              backgroundColor: dbStatus.connected ? '#16a34a' : '#dc2626',
              boxShadow: dbStatus.connected ? '0 0 6px #16a34a' : 'none',
            }}
          />
          <Database size={13} />
          <span>{dbStatus.connected ? 'Database: Live' : 'Database: Offline'}</span>
        </div>

        {/* Actions */}
        <div className="topbar-actions">
          {/* Search Button */}
          <button
            id="topbar-search-btn"
            className="topbar-icon-btn"
            aria-label="Search"
            title="Search applications, licenses, and users"
            onClick={() => {
              setSearchQuery('');
              setShowSearchModal(true);
            }}
          >
            <Search size={17} />
          </button>

          {/* Notifications Button */}
          <div style={{ position: 'relative' }}>
            <button
              id="topbar-notifications-btn"
              className="topbar-icon-btn"
              aria-label="Notifications"
              title="Notifications"
              onClick={() => setShowNotifications((v) => !v)}
            >
              <Bell size={17} />
              {hasUnreadNotifications && <span className="notification-dot" />}
            </button>

            {/* Notifications Popover Dropdown */}
            {showNotifications && (
              <>
                <div
                  style={{ position: 'fixed', inset: 0, zIndex: 150 }}
                  onClick={() => setShowNotifications(false)}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    right: 0,
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--border-radius-lg)',
                    boxShadow: 'var(--shadow-xl)',
                    width: 320,
                    zIndex: 200,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      padding: '12px 16px',
                      borderBottom: '1px solid var(--border-color)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>
                      Notifications
                    </div>
                    {hasUnreadNotifications && (
                      <button
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--primary-600)',
                          fontSize: 11,
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                        onClick={() => setHasUnreadNotifications(false)}
                      >
                        Mark all as read
                      </button>
                    )}
                  </div>

                  <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                    {notifications.map((n) => (
                      <div
                        key={n.id}
                        style={{
                          padding: '12px 16px',
                          borderBottom: '1px solid var(--border-color)',
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 10,
                          fontSize: 12,
                        }}
                      >
                        <div style={{ marginTop: 2 }}>
                          {n.type === 'warning' ? (
                            <AlertTriangle size={15} color="var(--warning-500)" />
                          ) : n.type === 'success' ? (
                            <CheckCircle size={15} color="var(--success-500)" />
                          ) : (
                            <Info size={15} color="var(--primary-500)" />
                          )}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                            {n.title}
                          </div>
                          <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4, fontSize: 11.5 }}>
                            {n.message}
                          </div>
                          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                            {n.time}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div
                    style={{
                      padding: '8px 16px',
                      background: 'var(--gray-50)',
                      textAlign: 'center',
                      fontSize: 11,
                      color: 'var(--text-muted)',
                    }}
                  >
                    All notifications are up to date
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Help & Info Button */}
          <button
            id="topbar-help-btn"
            className="topbar-icon-btn"
            aria-label="Help & Information"
            title="Help & Information"
            onClick={() => setShowHelpModal(true)}
          >
            <HelpCircle size={17} />
          </button>

          {/* User menu */}
          <div style={{ position: 'relative' }}>
            <button
              className="user-avatar-btn"
              onClick={() => setShowUserMenu((v) => !v)}
              aria-label="User menu"
              aria-expanded={showUserMenu}
            >
              <div className="avatar">{user?.avatar || 'U'}</div>
              <span className="user-info-name">{user?.name?.split(' ')[0]}</span>
            </button>

            {showUserMenu && (
              <>
                <div
                  style={{ position: 'fixed', inset: 0, zIndex: 150 }}
                  onClick={() => setShowUserMenu(false)}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    right: 0,
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--border-radius-lg)',
                    boxShadow: 'var(--shadow-lg)',
                    minWidth: 200,
                    zIndex: 200,
                    overflow: 'hidden',
                  }}
                >
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{user?.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{user?.email}</div>
                    {user?.provider && (
                      <div style={{ marginTop: 4, display: 'inline-block', fontSize: 11, padding: '2px 8px', borderRadius: 4, background: 'var(--primary-50)', color: 'var(--primary-700)', fontWeight: 500 }}>
                        SSO: {user.provider}
                      </div>
                    )}
                  </div>
                  <button
                    className="sidebar-item"
                    style={{ borderRadius: 0, margin: 0, padding: '10px 16px' }}
                    onClick={() => { setShowUserMenu(false); navigate('/settings'); }}
                  >
                    <Settings size={15} />
                    <span>Settings</span>
                  </button>
                  <button
                    className="sidebar-item"
                    style={{ borderRadius: 0, margin: 0, padding: '10px 16px', color: 'var(--danger-600)' }}
                    onClick={() => { logout(); navigate('/login'); }}
                  >
                    <LogOut size={15} />
                    <span>Sign Out</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Global Search Modal ────────────────────────────────────── */}
      <Modal
        open={showSearchModal}
        title="Global Portal Search"
        onClose={() => setShowSearchModal(false)}
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Press Esc or click outside to close
            </span>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowSearchModal(false)}>
              Close
            </button>
          </div>
        }
      >
        <div>
          <div className="input-with-icon" style={{ marginBottom: 14 }}>
            <span className="input-icon"><Search size={15} /></span>
            <input
              id="global-search-input"
              className="input"
              placeholder="Search tools, licenses, SKUs, or pages…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
              style={{ fontSize: 14, height: 38 }}
            />
          </div>

          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {filteredSearchResults.length === 0 ? (
              <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                No results found for "{searchQuery}".
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {filteredSearchResults.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 8,
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-card)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.15s ease',
                    }}
                    onClick={() => {
                      setShowSearchModal(false);
                      navigate(item.path);
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--gray-50)';
                      e.currentTarget.style.borderColor = 'var(--primary-300)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'var(--bg-card)';
                      e.currentTarget.style.borderColor = 'var(--border-color)';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <ToolLogo name={item.title} size={22} />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                          {item.title}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          {item.subtitle}
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Badge variant="neutral">{item.type}</Badge>
                      <ArrowRight size={13} color="var(--gray-400)" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Modal>

      {/* ── Help & Portal Information Modal ───────────────────────── */}
      <Modal
        open={showHelpModal}
        title="LicenseHub Management Portal Information"
        onClose={() => setShowHelpModal(false)}
        footer={
          <button className="btn btn-primary btn-sm" onClick={() => setShowHelpModal(false)}>
            Got it
          </button>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div
            style={{
              padding: 12,
              borderRadius: 8,
              background: 'var(--primary-50)',
              color: 'var(--primary-800)',
              fontSize: 12.5,
              lineHeight: 1.5,
              border: '1px solid var(--primary-200)',
            }}
          >
            <strong>LicenseHub</strong> is a centralized SaaS management system providing complete visibility into enterprise software applications, license tiers, and assigned user directories.
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ padding: '8px 12px', background: 'var(--gray-50)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>Dashboard Overview</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Displays monitored SaaS applications, active license tiers, assigned seat capacity, and renewal tracking.
              </div>
            </div>

            <div style={{ padding: '8px 12px', background: 'var(--gray-50)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>Application Directory</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Monitors active tools (Microsoft 365, Slack) and inactive tools (Lucidchart, Box, Zoom, Sofia, Jira, CATO) with direct links to license tiers.
              </div>
            </div>

            <div style={{ padding: '8px 12px', background: 'var(--gray-50)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>Grouped Licenses & Users</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Organizes licenses by application. Clicking any license opens the live assigned users list with search, department, and account statuses.
              </div>
            </div>

            <div style={{ padding: '8px 12px', background: 'var(--gray-50)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>Sync Connectors</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Live background connectors for Microsoft Graph API and Slack REST/SCIM keep seats and users in sync.
              </div>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
};
