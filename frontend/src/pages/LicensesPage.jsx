import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search, Plus, RefreshCw, Key, ChevronDown, ChevronUp, ChevronRight,
  AlertTriangle, CheckCircle, ShieldCheck, Shield, Cloud, Briefcase,
  Mail, Video, BarChart2, Zap, Code, ShieldAlert, TrendingUp,
  Headphones, Globe, Layers, Database, Bot, Sparkles, Filter,
  Users, UserCheck, X, ExternalLink, Copy, Check, MoreVertical,
  FileText, Send,
} from 'lucide-react';
import { Badge, Spinner, EmptyState, ProgressBar, Modal, AlertBanner, ToolLogo } from '../components/ui';
import { mockLicenses } from '../api/mockData';
import { useAuth } from '../context/AuthContext';
import {
  getLicenses, createLicense, triggerSync, getLicenseUsers, getAppAssignedUsers,
  getUsers, requestLicense,
} from '../api/services';
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
  const [departmentFilter, setDepartmentFilter] = useState('all');
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

  const departments = React.useMemo(() => {
    const set = new Set();
    users.forEach((u) => {
      if (u.department && u.department.trim()) set.add(u.department.trim());
    });
    return Array.from(set).sort();
  }, [users]);

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
    const matchesDept = departmentFilter === 'all' || u.department === departmentFilter;
    return matchesSearch && matchesStatus && matchesDept;
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
      maxWidth={760}
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

      {/* Search & Filters */}
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
        {departments.length > 0 && (
          <select
            className="select"
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            style={{ height: 34, fontSize: 13, maxWidth: 190 }}
          >
            <option value="all">All Departments ({departments.length})</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        )}
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
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Department</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Role</th>
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
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        padding: '3px 8px',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        background: 'var(--gray-100)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <Briefcase size={12} style={{ color: 'var(--primary-600)', flexShrink: 0 }} />
                      <span>{u.department || 'Enterprise'}</span>
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
                    {u.role || 'Member'}
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

// ── App-Level Users Modal (Admin / Users tiles) ──────────────────────────────
const ADMIN_ROLES = ['admin', 'owner', 'global admin', 'ceo', 'director', 'managing director', 'vice president', 'senior director', 'associate vice president'];
const isAdminRole = (role) => {
  if (!role) return false;
  const r = role.toLowerCase().trim();
  return ADMIN_ROLES.some((a) => r === a || r.includes('admin') || r.includes('owner'));
};

const AppUsersModal = ({ open, appName, roleFilter, users, onClose }) => {
  const [userSearch, setUserSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [copiedEmail, setCopiedEmail] = useState('');

  if (!open || !appName) return null;

  const title = roleFilter === 'admin' ? `${appName} — Admins` : `${appName} — All Users`;

  const displayUsers = roleFilter === 'admin'
    ? users.filter((u) => isAdminRole(u.role))
    : users;

  const departments = React.useMemo(() => {
    const set = new Set();
    displayUsers.forEach((u) => {
      if (u.department && u.department.trim()) set.add(u.department.trim());
    });
    return Array.from(set).sort();
  }, [displayUsers]);

  const filteredUsers = displayUsers.filter((u) => {
    const q = userSearch.toLowerCase();
    const matchesSearch =
      !q ||
      u.name?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q) ||
      u.department?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q);
    const matchesDept = departmentFilter === 'all' || u.department === departmentFilter;
    return matchesSearch && matchesDept;
  });

  const handleCopyEmail = (email) => {
    navigator.clipboard?.writeText(email);
    setCopiedEmail(email);
    setTimeout(() => setCopiedEmail(''), 2000);
  };

  return (
    <Modal
      open={open}
      title=""
      maxWidth={820}
      onClose={onClose}
      footer={<button className="btn btn-secondary" onClick={onClose}>Close</button>}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <ToolLogo name={appName} size={42} />
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
            {title}
          </h3>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
            {displayUsers.length} {roleFilter === 'admin' ? 'administrators' : 'users'} · sourced from license_assigned_users
          </div>
        </div>
      </div>

      {/* Summary Badges */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <Badge variant={roleFilter === 'admin' ? 'info' : 'success'}>
          {roleFilter === 'admin' ? <Shield size={12} /> : <Users size={12} />}
          <span style={{ marginLeft: 4 }}>{displayUsers.length} {roleFilter === 'admin' ? 'Admins' : 'Total Users'}</span>
        </Badge>
        <Badge variant="neutral">
          {displayUsers.filter((u) => u.status === 'active').length} Active
        </Badge>
      </div>

      {/* Search & Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <div className="input-with-icon" style={{ flex: 1, minWidth: 200 }}>
          <span className="input-icon"><Search size={14} /></span>
          <input
            className="input"
            placeholder="Search by name, email, department, role…"
            value={userSearch}
            onChange={(e) => setUserSearch(e.target.value)}
            style={{ height: 34, fontSize: 13 }}
          />
        </div>
        {departments.length > 0 && (
          <select
            className="select"
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            style={{ height: 34, fontSize: 13, maxWidth: 190 }}
          >
            <option value="all">All Departments ({departments.length})</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        )}
      </div>

      {/* Table */}
      {filteredUsers.length === 0 ? (
        <EmptyState
          icon={<Users size={22} color="var(--gray-400)" />}
          title="No users found"
          description={userSearch ? 'No users match your search.' : `No ${roleFilter === 'admin' ? 'administrators' : 'users'} for this application.`}
        />
      ) : (
        <div style={{ maxHeight: 380, overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 8 }}>
          <table className="table" style={{ margin: 0 }}>
            <thead>
              <tr style={{ background: 'var(--gray-50)', position: 'sticky', top: 0, zIndex: 1 }}>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>User</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Department</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Role</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>License</th>
                <th style={{ padding: '8px 12px', fontSize: 11 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u, idx) => (
                <tr key={u.user_id || u.email || idx}>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div
                        style={{
                          width: 30, height: 30, borderRadius: '50%',
                          background: roleFilter === 'admin'
                            ? 'linear-gradient(135deg, #2563eb, #1e40af)'
                            : 'linear-gradient(135deg, var(--primary-500), var(--primary-700))',
                          color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: 600, fontSize: 12, flexShrink: 0,
                        }}
                      >
                        {u.name?.charAt(0)?.toUpperCase() || 'U'}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{u.name}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.email}</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleCopyEmail(u.email); }}
                            title="Copy email"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: copiedEmail === u.email ? 'var(--success-600)' : 'var(--gray-400)' }}
                          >
                            {copiedEmail === u.email ? <Check size={11} /> : <Copy size={11} />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        padding: '3px 8px',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        background: 'var(--gray-100)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <Briefcase size={12} style={{ color: 'var(--primary-600)', flexShrink: 0 }} />
                      <span>{u.department || 'Enterprise'}</span>
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
                    {u.role || 'Member'}
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: 'var(--text-secondary)' }}>
                    {u.license_name || '—'}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
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
    </Modal>
  );
};

// ── Request License Modal ────────────────────────────────────────────────────
const STANDARD_DEPARTMENTS = [
  'Software Engineering',
  'Product Engineering',
  'IT Operations',
  'SRE Team',
  'US Staffing',
  'US Staffing Team',
  'Business Development',
  'Sales',
  'Sales - MLY',
  'Marketing',
  'Operations',
  'Finance & Accounting',
  'Human Resources',
  'Legal & Compliance',
  'Cybersecurity & Infrastructure',
  'Quality Assurance',
  'Customer Support',
  'Design & UX',
  'Innovation & AI',
  'Executive Management',
];

export const RequestLicenseModal = ({
  open,
  licenses,
  users,
  onClose,
  onSubmitSuccess,
  submitRequest = requestLicense,
  submissionDisabled = false,
}) => {
  const [selectedUserKey, setSelectedUserKey] = useState('');
  const [department, setDepartment] = useState('');
  const [isAutoFilledDept, setIsAutoFilledDept] = useState(false);
  const [selectedLicenseId, setSelectedLicenseId] = useState('');
  const [businessJustification, setBusinessJustification] = useState('');
  const [urgency, setUrgency] = useState('Standard');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const submissionInProgress = React.useRef(false);
  const idempotencyKey = React.useRef('');

  // Deduplicate and sort users
  const userOptions = React.useMemo(() => {
    const map = new Map();
    (users || []).forEach((u) => {
      const email = (u.email || '').trim().toLowerCase();
      const name = (u.name || u.display_name || '').trim();
      const key = email || name.toLowerCase();
      if (key && !map.has(key)) {
        map.set(key, {
          key,
          id: u.user_id,
          name: name || 'User',
          email: u.email || '',
          department: (u.department || '').trim(),
          role: u.role || 'Member',
        });
      }
    });
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [users]);

  // Aggregate all unique departments
  const departmentOptions = React.useMemo(() => {
    const set = new Set(STANDARD_DEPARTMENTS);
    (users || []).forEach((u) => {
      if (u.department && u.department.trim()) {
        set.add(u.department.trim());
      }
    });
    return Array.from(set).sort();
  }, [users]);

  // Selected user object
  const selectedUser = React.useMemo(() => {
    if (!selectedUserKey) return null;
    return userOptions.find((u) => u.key === selectedUserKey) || null;
  }, [selectedUserKey, userOptions]);

  // When user is selected from dropdown
  const handleUserChange = (key) => {
    setSelectedUserKey(key);
    setFormError('');
    const user = userOptions.find((u) => u.key === key);
    if (user && user.department && user.department.toLowerCase() !== 'enterprise') {
      setDepartment(user.department);
      setIsAutoFilledDept(true);
    } else if (user && user.department) {
      setDepartment(user.department);
      setIsAutoFilledDept(true);
    } else {
      setDepartment('');
      setIsAutoFilledDept(false);
    }
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (submissionDisabled || submissionInProgress.current) return;
    if (!selectedUser) {
      setFormError('Please select a user to request this license for.');
      return;
    }
    if (!department.trim()) {
      setFormError('Please select or specify a department for this user.');
      return;
    }
    if (!selectedLicenseId) {
      setFormError('Please select the software license to request.');
      return;
    }
    if (!businessJustification.trim()) {
      setFormError('Please provide a business justification for this request.');
      return;
    }

    const chosenLic = (licenses || []).find(
      (l) => String(l.license_id || l.sku_id || l.id) === String(selectedLicenseId)
    );
    if (!idempotencyKey.current) idempotencyKey.current = crypto.randomUUID();

    const payload = {
      user_id: selectedUser.id,
      idempotency_key: idempotencyKey.current,
      user_name: selectedUser.name,
      user_email: selectedUser.email,
      department: department.trim(),
      application_name: chosenLic?.application_name || 'Application',
      license_id: chosenLic?.db_license_id || chosenLic?.license_id || selectedLicenseId,
      license_name: chosenLic?.license_name || chosenLic?.product || selectedLicenseId,
      license_type: chosenLic?.license_type || '',
      business_justification: businessJustification.trim(),
      urgency,
      requested_at: new Date().toISOString(),
    };

    submissionInProgress.current = true;
    setSubmitting(true);
    try {
      const savedRequest = await submitRequest(payload);
      onSubmitSuccess?.(savedRequest, payload);
      // Reset
      setSelectedUserKey('');
      setDepartment('');
      setSelectedLicenseId('');
      setBusinessJustification('');
      setFormError('');
      idempotencyKey.current = '';
      onClose();
    } catch (err) {
      setFormError(
        err.response?.data?.detail
          || 'Failed to submit license request. Please try again.'
      );
    } finally {
      submissionInProgress.current = false;
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <Modal
      open={open}
      title=""
      maxWidth={680}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={submitting || submissionDisabled}
          >
            <Send size={14} />
            {submissionDisabled
              ? 'Submission Unavailable'
              : submitting
                ? 'Submitting Request...'
                : 'Submit License Request'}
          </button>
        </>
      }
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: 'linear-gradient(135deg, var(--primary-600), var(--primary-800))',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: '0 4px 10px rgba(37,99,235,0.2)',
          }}
        >
          <Key size={22} />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: 'var(--text-primary)' }}>
            Request License
          </h3>
          <p style={{ margin: '3px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>
            Submit a license provisioning request for a team member with business justification
          </p>
        </div>
      </div>

      {formError && (
        <div style={{ marginBottom: 14 }}>
          <AlertBanner type="error" message={formError} onDismiss={() => setFormError('')} />
        </div>
      )}

      {submissionDisabled && (
        <AlertBanner
          type="warning"
          message="This shared account does not identify an employee. Request submission is restricted to an individually authorized account."
        />
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* 1. User Name Selection Dropdown */}
        <div>
          <label className="label" style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Users size={14} color="var(--primary-600)" />
            User Name <span style={{ color: 'var(--danger-500)' }}>*</span>
          </label>
          <select
            className="select"
            value={selectedUserKey}
            onChange={(e) => handleUserChange(e.target.value)}
            style={{ width: '100%', height: 40, fontSize: 13 }}
            autoFocus
          >
            <option value="">-- Select a User ({userOptions.length} available) --</option>
            {userOptions.map((u) => (
              <option key={u.key} value={u.key}>
                {u.name} — {u.email} {u.department ? `[${u.department}]` : ''}
              </option>
            ))}
          </select>

          {selectedUser && (
            <div
              style={{
                marginTop: 8,
                padding: '8px 12px',
                borderRadius: 8,
                background: 'var(--gray-50)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: 12,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: '50%',
                    background: 'var(--primary-600)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: 11,
                  }}
                >
                  {selectedUser.name?.charAt(0)?.toUpperCase()}
                </div>
                <div>
                  <span style={{ fontWeight: 600 }}>{selectedUser.name}</span>
                  <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>{selectedUser.email}</span>
                </div>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)', background: 'white', padding: '2px 8px', borderRadius: 4, border: '1px solid var(--border-color)' }}>
                {selectedUser.role || 'Member'}
              </span>
            </div>
          )}
        </div>

        {/* 2. Department Dropdown (Auto-selected if available, selectable from dropdown if not) */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <label className="label" style={{ margin: 0, fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Briefcase size={14} color="var(--primary-600)" />
              Department <span style={{ color: 'var(--danger-500)' }}>*</span>
            </label>
            {isAutoFilledDept && department && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#15803d',
                  background: '#dcfce7',
                  padding: '2px 8px',
                  borderRadius: 6,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <Check size={11} /> Auto-selected from profile
              </span>
            )}
          </div>
          <select
            className="select"
            value={department}
            onChange={(e) => {
              setDepartment(e.target.value);
              setIsAutoFilledDept(false);
            }}
            style={{ width: '100%', height: 40, fontSize: 13 }}
          >
            <option value="">-- Select Department --</option>
            {departmentOptions.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
          {selectedUser && !department && (
            <div style={{ fontSize: 11, color: 'var(--warning-600)', marginTop: 4 }}>
              User does not have a department on record. Please select their department above.
            </div>
          )}
        </div>

        {/* 3. License Selection Dropdown */}
        <div>
          <label className="label" style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Key size={14} color="var(--primary-600)" />
            Requested License <span style={{ color: 'var(--danger-500)' }}>*</span>
          </label>
          <select
            className="select"
            value={selectedLicenseId}
            onChange={(e) => setSelectedLicenseId(e.target.value)}
            style={{ width: '100%', height: 40, fontSize: 13 }}
          >
            <option value="">-- Select License to Request --</option>
            {licenses.map((lic) => {
              const id = lic.license_id || lic.sku_id || lic.id;
              const avail = lic.available_quantity;
              return (
                <option key={id} value={id}>
                  {lic.application_name} — {lic.license_name || lic.product} {avail !== undefined ? `(${avail} seats available)` : ''}
                </option>
              );
            })}
          </select>
        </div>

        {/* 4. Business Justification Textarea */}
        <div>
          <label className="label" style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
            <FileText size={14} color="var(--primary-600)" />
            Business Justification <span style={{ color: 'var(--danger-500)' }}>*</span>
          </label>
          <textarea
            className="input"
            rows={3}
            placeholder="Explain why this license is needed (e.g. project deliverables, client requirements, role transition, specific software access)..."
            value={businessJustification}
            onChange={(e) => setBusinessJustification(e.target.value)}
            style={{
              width: '100%',
              minHeight: 85,
              padding: '10px 12px',
              fontSize: 13,
              borderRadius: 8,
              resize: 'vertical',
              fontFamily: 'inherit',
            }}
          />
        </div>

        {/* 5. Request Urgency Indicator */}
        <div>
          <label className="label" style={{ fontWeight: 600, fontSize: 12, marginBottom: 6, color: 'var(--text-muted)' }}>
            Request Urgency
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            {['Standard', 'Urgent', 'Immediate Project Blocker'].map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setUrgency(level)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: urgency === level ? 600 : 500,
                  border: urgency === level ? '1.5px solid var(--primary-600)' : '1px solid var(--border-color)',
                  background: urgency === level ? 'var(--primary-50)' : 'white',
                  color: urgency === level ? 'var(--primary-700)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </form>
    </Modal>
  );
};

// ── App Hero Header Banner Component (Matches Template Card) ───────────────
const APP_DESCRIPTIONS = {
  'Microsoft 365': 'Productivity tools, collaboration, and cloud services for your organization.',
  'Slack': 'Real-time team messaging, channels, and workplace integration platform.',
  'Lucidchart': 'Diagramming, flowcharts, and visual workspace for architecture & design.',
  'Box': 'Secure cloud content management, file sharing, and storage solution.',
  'Zoom': 'Video conferencing, webinars, and virtual meeting platform.',
  'Sofia - (Pilot)': 'AI-powered enterprise virtual assistant and automation platform.',
  '_Jira': 'Agile project tracking, issue management, and software workflow platform.',
  'CATO': 'Cloud-native SASE network security and zero-trust framework.',
};

const AppHeroCard = ({
  appName,
  appLicenses,
  appUserCounts,
  onOpenAdminModal,
  onOpenUsersModal,
  onManageLicenses,
}) => {
  const totalPurchased = appLicenses.reduce((acc, l) => acc + (l.total_quantity || 0), 0);
  const totalAssigned = appLicenses.reduce((acc, l) => acc + (l.allocated_quantity || l.used_quantity || 0), 0);
  const totalAvailable = Math.max(0, totalPurchased - totalAssigned);
  const utilPct = totalPurchased > 0 ? Math.min(100, Math.round((totalAssigned / totalPurchased) * 100)) : 0;
  const isActive = appLicenses.length > 0 ? appLicenses.some((l) => l.status === 'active') : true;
  const description = APP_DESCRIPTIONS[appName] || 'Enterprise software application license management and seat allocation.';

  const adminCount = appUserCounts[appName]?.admins ?? (appName === 'Microsoft 365' ? 31 : appName === 'Slack' ? 4 : 0);
  const totalUserCount = appUserCounts[appName]?.total ?? (totalAssigned || (appName === 'Microsoft 365' ? 999 : appName === 'Slack' ? 42 : 0));

  // Circular Donut SVG Parameters
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (circumference * utilPct) / 100;

  // Usage Health Rating
  const getHealthInfo = (pct) => {
    if (pct >= 95) return { label: 'High Usage', color: '#ea580c', text: 'Seat capacity near full utilization.' };
    if (pct >= 50) return { label: 'Good', color: '#16a34a', text: 'Your license usage is healthy.' };
    if (pct > 0) return { label: 'Optimal', color: '#2563eb', text: 'License capacity readily available.' };
    return { label: 'Pending', color: '#64748b', text: 'Software integration idle.' };
  };
  const health = getHealthInfo(utilPct);

  return (
    <div
      className="app-hero-header-grid"
      style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        borderBottom: '1px solid var(--border-color)',
        display: 'grid',
        gridTemplateColumns: '1.25fr 1fr 0.85fr 0.9fr',
        gap: 20,
        alignItems: 'center',
      }}
    >
      {/* Panel 1: App Identity & Description */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ToolLogo name={appName} size={42} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                {appName}
              </h2>
              <Badge variant={isActive ? 'success' : 'neutral'}>
                {isActive ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              {appLicenses.length} {appLicenses.length === 1 ? 'license tier' : 'license tiers'}
            </div>
          </div>
        </div>

        <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '4px 0 6px 0', lineHeight: 1.45 }}>
          {description}
        </p>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => onOpenUsersModal(appName)}
            style={{ borderRadius: 8, padding: '6px 14px', fontSize: 12, fontWeight: 600 }}
          >
            View Details
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={onManageLicenses}
            style={{ borderRadius: 8, padding: '6px 14px', fontSize: 12, fontWeight: 500, background: 'white', border: '1px solid var(--border-color)' }}
          >
            Manage Licenses
          </button>
        </div>
      </div>

      {/* Panel 2: Utilization Circular Donut & Seat Breakdown */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '14px 16px',
          background: 'white',
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        }}
      >
        <div style={{ position: 'relative', width: 84, height: 84, flexShrink: 0 }}>
          <svg width="84" height="84" viewBox="0 0 90 90">
            <circle cx="45" cy="45" r={radius} fill="transparent" stroke="#e2e8f0" strokeWidth="9" />
            <circle
              cx="45"
              cy="45"
              r={radius}
              fill="transparent"
              stroke="#2563eb"
              strokeWidth="9"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform="rotate(-90 45 45)"
              style={{ transition: 'stroke-dashoffset 0.5s ease' }}
            />
            <text x="45" y="42" textAnchor="middle" fontSize="16" fontWeight="800" fill="var(--gray-900)">
              {utilPct}%
            </text>
            <text x="45" y="55" textAnchor="middle" fontSize="9" fontWeight="500" fill="var(--gray-500)">
              Utilization
            </text>
          </svg>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#2563eb' }} />
            <span style={{ fontWeight: 700, color: 'var(--gray-900)' }}>{formatNumber(totalAssigned)}</span>
            <span style={{ color: 'var(--gray-500)', fontSize: 11 }}>Assigned</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#cbd5e1' }} />
            <span style={{ fontWeight: 700, color: 'var(--gray-900)' }}>{formatNumber(totalAvailable)}</span>
            <span style={{ color: 'var(--gray-500)', fontSize: 11 }}>Available</span>
          </div>
          <div style={{ marginTop: 2, paddingTop: 4, borderTop: '1px solid #f1f5f9', fontSize: 12 }}>
            <span style={{ fontWeight: 800, color: 'var(--gray-900)' }}>{formatNumber(totalPurchased)}</span>{' '}
            <span style={{ fontWeight: 500, color: 'var(--gray-500)', fontSize: 11 }}>Total Seats</span>
          </div>
        </div>
      </div>

      {/* Panel 3: Admin & Users Stacked Tiles */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {/* Admin Tile */}
        <button
          className="admin-tile-btn"
          onClick={() => onOpenAdminModal(appName)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 14px',
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: 12,
            cursor: 'pointer',
            width: '100%',
            textAlign: 'left',
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              background: 'linear-gradient(135deg, #2563eb, #1e40af)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Shield size={17} color="white" />
          </div>
          <div style={{ flex: 1, lineHeight: 1.2 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#1e3a8a' }}>Admin</div>
            <div style={{ fontSize: 11, color: '#3b82f6', fontWeight: 500 }}>
              {adminCount} {adminCount === 1 ? 'Admin' : 'Admins'}
            </div>
          </div>
          <ChevronRight size={15} color="#3b82f6" />
        </button>

        {/* Users Tile */}
        <button
          className="users-tile-btn"
          onClick={() => onOpenUsersModal(appName)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 14px',
            background: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: 12,
            cursor: 'pointer',
            width: '100%',
            textAlign: 'left',
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              background: 'linear-gradient(135deg, #16a34a, #15803d)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Users size={17} color="white" />
          </div>
          <div style={{ flex: 1, lineHeight: 1.2 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#14532d' }}>Users</div>
            <div style={{ fontSize: 11, color: '#16a34a', fontWeight: 500 }}>
              {totalUserCount} {totalUserCount === 1 ? 'User' : 'Users'}
            </div>
          </div>
          <ChevronRight size={15} color="#16a34a" />
        </button>
      </div>

      {/* Panel 4: License Health Indicator */}
      <div
        style={{
          padding: '14px 16px',
          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
          border: '1px solid #e2e8f0',
          borderRadius: 12,
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            License Health
          </span>
          <span style={{ fontSize: 12, color: 'var(--gray-400)', cursor: 'pointer' }} title="Overall usage health rating">ⓘ</span>
        </div>

        <div style={{ fontSize: 20, fontWeight: 800, color: health.color }}>
          {health.label}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 2 }}>
          <div style={{ flex: 1, height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${utilPct}%`, background: health.color, borderRadius: 4, transition: 'width 0.4s ease' }} />
          </div>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--gray-800)' }}>{utilPct}%</span>
        </div>

        <div style={{ fontSize: 11, color: 'var(--gray-500)', marginTop: 2 }}>
          {health.text}
        </div>
      </div>
    </div>
  );
};

// ── Main Licenses Page ────────────────────────────────────────────────────────
const LicensesPage = () => {
  const { user } = useAuth();
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
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);
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
  const [appUsersModal, setAppUsersModal] = useState(null); // { appName, roleFilter, users }
  const [appUserCounts, setAppUserCounts] = useState({}); // { 'Microsoft 365': { admins: N, total: N, users: [] }, ... }

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
    getUsers()
      .then((res) => {
        if (res.data && Array.isArray(res.data)) {
          setAvailableUsers(res.data);
        }
      })
      .catch((err) => {
        console.warn('Could not load users for license request modal:', err);
      });
  }, []);

  // Aggregated unique users for Request License modal
  const allUsersForRequest = React.useMemo(() => {
    const list = [...availableUsers];
    Object.values(appUserCounts).forEach((c) => {
      if (c?.users && Array.isArray(c.users)) {
        list.push(...c.users);
      }
    });
    return list;
  }, [availableUsers, appUserCounts]);

  const handleRequestLicenseSuccess = (savedRequest, submittedDetails) => {
    const details = {
      ...submittedDetails,
      user_name: savedRequest.employee_name || submittedDetails.user_name,
      license_name: savedRequest.license_name || submittedDetails.license_name,
      department: savedRequest.department || submittedDetails.department,
    };
    setSuccess(
      `License request ${savedRequest.request_id} for ${details.user_name} (${details.license_name}) has been saved for the ${details.department} department.`
    );
    setTimeout(() => setSuccess(''), 5500);
  };

  // Fetch admin/user counts for active applications
  useEffect(() => {
    const fetchAppUsers = async () => {
      const activeApps = ['Microsoft 365', 'Slack'];
      const counts = {};
      for (const app of activeApps) {
        try {
          const users = await getAppAssignedUsers(app);
          const admins = users.filter((u) => isAdminRole(u.role));
          counts[app] = { admins: admins.length, total: users.length, users };
        } catch {
          counts[app] = { admins: 0, total: 0, users: [] };
        }
      }
      setAppUserCounts(counts);
    };
    fetchAppUsers();
  }, [licenses]);

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
            id="licenses-request-btn"
            className="btn btn-primary btn-sm"
            onClick={() => setShowRequestModal(true)}
          >
            <Key size={14} /> Request License
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
            return (
              <div
                key={appName}
                className="card"
                style={{
                  overflow: 'hidden',
                  border: '1px solid var(--border-color)',
                  boxShadow: 'var(--shadow-sm)',
                  borderRadius: 16,
                  marginBottom: 20,
                }}
              >
                {/* ── Application Hero Header Banner ── */}
                <AppHeroCard
                  appName={appName}
                  appLicenses={appLicenses}
                  appUserCounts={appUserCounts}
                  onOpenAdminModal={(name) => {
                    const cached = appUserCounts[name];
                    if (cached) {
                      setAppUsersModal({ appName: name, roleFilter: 'admin', users: cached.users });
                    } else {
                      getAppAssignedUsers(name).then((users) => {
                        setAppUsersModal({ appName: name, roleFilter: 'admin', users });
                      });
                    }
                  }}
                  onOpenUsersModal={(name) => {
                    const cached = appUserCounts[name];
                    if (cached) {
                      setAppUsersModal({ appName: name, roleFilter: 'all', users: cached.users });
                    } else {
                      getAppAssignedUsers(name).then((users) => {
                        setAppUsersModal({ appName: name, roleFilter: 'all', users });
                      });
                    }
                  }}
                  onManageLicenses={() => setShowAddModal(true)}
                />

                {/* ── Licenses Table for this Application ── */}
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
                        <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                          <th style={{ textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>LICENSE / SKU</th>
                          <th style={{ textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>CATEGORY</th>
                          <th style={{ textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>ASSIGNED SEATS</th>
                          <th style={{ textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>UTILIZATION</th>
                          <th style={{ textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>EXPIRY DATE</th>
                          <th style={{ textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>STATUS</th>
                          <th style={{ textAlign: 'right', textTransform: 'uppercase', fontSize: 11, letterSpacing: '0.04em', color: 'var(--gray-500)' }}>ACTIONS</th>
                        </tr>
                      </thead>
                      <tbody>
                        {appLicenses.map((lic) => {
                          const total = lic.total_quantity || 0;
                          const assigned = lic.allocated_quantity || lic.used_quantity || 0;
                          const available = Math.max(0, total - assigned);
                          const utilPct = total ? Math.min(100, Math.round((assigned / total) * 100)) : 0;
                          const IconComponent = CATEGORY_ICONS[lic.license_type] || Key;

                          // Utilization Bar Color Logic matching template image
                          const getBarColor = (pct) => {
                            if (pct >= 95) return '#ef4444'; // Red for 100%
                            if (pct >= 75) return '#f97316'; // Orange for ~80%
                            if (pct > 0) return '#2563eb';   // Blue
                            return '#cbd5e1';               // Gray for 0%
                          };
                          const barColor = getBarColor(utilPct);

                          return (
                            <tr
                              key={lic.license_id}
                              style={{ cursor: 'pointer' }}
                              onClick={() => setSelectedLicense(lic)}
                              className="license-row-clickable"
                            >
                              <td>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                  <div
                                    style={{
                                      width: 32,
                                      height: 32,
                                      borderRadius: 8,
                                      background: '#f1f5f9',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      flexShrink: 0,
                                    }}
                                  >
                                    <ToolLogo name={lic.application_name} size={20} />
                                  </div>
                                  <div>
                                    <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--gray-900)' }}>
                                      {lic.license_name}
                                    </div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace', textTransform: 'uppercase' }}>
                                      {lic.raw_sku_part_number || lic.product_code || '—'}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span style={{ fontSize: 12, fontWeight: 500, color: '#334155' }}>
                                  {lic.license_type || 'Commercial'}
                                </span>
                              </td>
                              <td>
                                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--gray-900)' }}>
                                  {formatNumber(assigned)} <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>/ {formatNumber(total)}</span>
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                  {formatNumber(available)} available
                                </div>
                              </td>
                              <td style={{ minWidth: 140 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--gray-800)', minWidth: 38 }}>
                                    {utilPct}%
                                  </span>
                                  <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
                                    <div
                                      style={{
                                        height: '100%',
                                        width: `${utilPct}%`,
                                        background: barColor,
                                        borderRadius: 3,
                                      }}
                                    />
                                  </div>
                                </div>
                              </td>
                              <td>
                                <div style={{ fontSize: 12, color: 'var(--gray-800)', fontWeight: 500 }}>
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
                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                                  <button
                                    className="btn btn-secondary btn-sm"
                                    style={{
                                      borderRadius: 6,
                                      fontSize: 12,
                                      padding: '4px 12px',
                                      fontWeight: 500,
                                      background: 'white',
                                      border: '1px solid var(--border-color)',
                                    }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setSelectedLicense(lic);
                                    }}
                                  >
                                    View Users
                                  </button>
                                  <button
                                    className="btn btn-icon btn-sm"
                                    style={{ color: 'var(--gray-400)', padding: 4 }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setSelectedLicense(lic);
                                    }}
                                    title="More options"
                                  >
                                    <MoreVertical size={15} />
                                  </button>
                                </div>
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

      {/* App Users Modal (Admin / Users tiles) */}
      <AppUsersModal
        open={!!appUsersModal}
        appName={appUsersModal?.appName}
        roleFilter={appUsersModal?.roleFilter}
        users={appUsersModal?.users || []}
        onClose={() => setAppUsersModal(null)}
      />

      {/* Request License Modal */}
      <RequestLicenseModal
        open={showRequestModal}
        licenses={licenses}
        users={allUsersForRequest}
        onClose={() => setShowRequestModal(false)}
        onSubmitSuccess={handleRequestLicenseSuccess}
        submissionDisabled={
          !user?.roles?.includes('License.Requester')
          && !user?.roles?.includes('License.Admin')
        }
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

      {/* App-Level Users Modal (Admin / Users Tiles) */}
      <AppUsersModal
        open={!!appUsersModal}
        appName={appUsersModal?.appName}
        roleFilter={appUsersModal?.roleFilter}
        users={appUsersModal?.users || []}
        onClose={() => setAppUsersModal(null)}
      />
    </>
  );
};

export default LicensesPage;
