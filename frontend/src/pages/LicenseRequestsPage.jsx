import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  FileText,
  Plus,
  ShieldCheck,
  UserRound,
  X,
  XCircle,
} from 'lucide-react';
import {
  AlertBanner,
  EmptyState,
  Spinner,
} from '../components/ui';
import {
  decideLicenseRequest,
  getLicenseRequest,
  getLicenseRequestOptions,
  getLicenseRequests,
  requestLicense,
} from '../api/services';
import { useAuth } from '../context/AuthContext';
import { RequestLicenseModal } from './LicensesPage';

const formatDateTime = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString();
};

const RequestDetailsDrawer = ({ request, onClose, onDecision }) => {
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [decisionComments, setDecisionComments] = useState('');
  const [savingDecision, setSavingDecision] = useState(false);

  const load = useCallback(async () => {
    setError('');
    try {
      const result = await getLicenseRequest(request.request_id);
      setDetail(result.data);
    } catch (loadError) {
      console.error('Failed to load license request detail:', loadError);
      setError(
        loadError.response?.data?.detail
          || 'Unable to load this request. Check your access and try again.'
      );
    } finally {
      setLoading(false);
    }
  }, [request.request_id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDecision = async (decision) => {
    setSavingDecision(true);
    setError('');
    try {
      const result = await decideLicenseRequest(
        request.request_id,
        decision,
        decisionComments.trim() || undefined
      );
      setDetail(result.data);
      setDecisionComments('');
      onDecision(result.data);
    } catch (decisionError) {
      console.error('Failed to save approval decision:', decisionError);
      setError(
        decisionError.response?.data?.detail
          || 'The approval decision could not be saved.'
      );
    } finally {
      setSavingDecision(false);
    }
  };

  const approval = detail?.approvals?.find(
    (item) => item.stage === 'Department / Tower Head Approval'
  );
  const approvalIcon = (status) => {
    if (status === 'Approved' || status === 'Completed') return <CheckCircle2 size={18} />;
    if (status === 'Rejected') return <XCircle size={18} />;
    return <Clock3 size={18} />;
  };

  return (
    <div className="request-drawer-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <aside className="request-drawer" role="dialog" aria-modal="true" aria-labelledby="request-drawer-title">
        <header className="request-drawer-header">
          <div>
            <div className="request-drawer-eyebrow">License request</div>
            <h2 id="request-drawer-title">{request.request_id}</h2>
          </div>
          <button className="topbar-icon-btn" onClick={onClose} aria-label="Close details">
            <X size={18} />
          </button>
        </header>

        <div className="request-drawer-content">
          {loading && <Spinner size={28} />}
          {error && <AlertBanner type="error" message={error} onDismiss={() => setError('')} />}
          {!loading && detail && (
            <>
              <section className="request-detail-section">
                <h3><FileText size={16} /> Request Details</h3>
                <dl className="request-detail-grid">
                  <dt>Employee</dt><dd>{detail.employee_name} <span>{detail.employee_email}</span></dd>
                  <dt>Department</dt><dd>{detail.department}</dd>
                  <dt>Application</dt><dd>{detail.application}</dd>
                  <dt>License type</dt><dd>{detail.license_type || detail.license_name || '—'}</dd>
                  <dt>Business justification</dt><dd>{detail.business_justification}</dd>
                  <dt>Submitted</dt><dd>{formatDateTime(detail.requested_at)}</dd>
                  <dt>Current status</dt><dd><span className="badge badge-primary">{detail.status}</span></dd>
                  <dt>Approver</dt><dd>{detail.approver_name || 'No approver assigned'}</dd>
                </dl>
              </section>

              <section className="request-detail-section">
                <h3><ShieldCheck size={16} /> Approval Flow</h3>
                <ol className="approval-timeline">
                  <li className="approval-timeline-item complete">
                    <span className="approval-timeline-icon"><CheckCircle2 size={18} /></span>
                    <div>
                      <strong>Request Submitted</strong>
                      <p>
                        {detail.test_mode
                          ? `Recorded by the shared development account for ${detail.employee_name}.`
                          : `${detail.employee_name} submitted this request.`}
                      </p>
                      <time>{formatDateTime(detail.requested_at)}</time>
                    </div>
                  </li>
                  {approval && (
                    <li className={`approval-timeline-item ${approval.decision.toLowerCase()}`}>
                      <span className="approval-timeline-icon">{approvalIcon(approval.decision)}</span>
                      <div>
                        <strong>{approval.stage}</strong>
                        <p>{approval.approver_name} · {approval.decision}</p>
                        {approval.decision_at && (
                          <time>{formatDateTime(approval.decision_at)}</time>
                        )}
                        {approval.comments && <blockquote>{approval.comments}</blockquote>}
                      </div>
                    </li>
                  )}
                  {!approval && detail.test_mode && (
                    <li className="approval-timeline-item pending">
                      <span className="approval-timeline-icon"><Clock3 size={18} /></span>
                      <div>
                        <strong>Tower Head Approval</strong>
                        <p>Pending · Test workflow preview; no approver decision is recorded.</p>
                      </div>
                    </li>
                  )}
                  {detail.provisioning_status && (
                    <li className={`approval-timeline-item ${detail.provisioning_status.toLowerCase().replaceAll(' ', '-')}`}>
                      <span className="approval-timeline-icon">{approvalIcon(detail.provisioning_status)}</span>
                      <div>
                        <strong>IT / License Provisioning</strong>
                        <p>{detail.provisioning_status}</p>
                      </div>
                    </li>
                  )}
                  {!detail.provisioning_status && detail.test_mode && (
                    <li className="approval-timeline-item pending">
                      <span className="approval-timeline-icon"><Clock3 size={18} /></span>
                      <div>
                        <strong>License Provisioning</strong>
                        <p>Pending · Test workflow preview; provisioning has not started.</p>
                      </div>
                    </li>
                  )}
                  {detail.status === 'Completed' && (
                    <li className="approval-timeline-item complete">
                      <span className="approval-timeline-icon"><CheckCircle2 size={18} /></span>
                      <div><strong>Request Completed</strong></div>
                    </li>
                  )}
                </ol>
                {!approval && (
                  <p className="request-history-empty">
                    {detail.test_mode
                      ? 'The timeline stages below are a test preview, not approval history.'
                      : 'No approval stage is recorded for this request.'}
                  </p>
                )}
                {!detail.provisioning_status && (
                  !detail.test_mode && (
                    <p className="request-workflow-note">
                      IT provisioning is not configured for this request.
                    </p>
                  )
                )}
              </section>

              <section className="request-detail-section">
                <h3><UserRound size={16} /> Approval History</h3>
                {detail.approvals?.length ? (
                  <div className="approval-history-list">
                    {detail.approvals.map((item) => (
                      <article className="approval-history-item" key={item.id}>
                        <div>
                          <strong>{item.approver_name}</strong>
                          <span>{item.stage}</span>
                        </div>
                        <span className={`badge ${item.decision === 'Rejected' ? 'badge-danger' : item.decision === 'Approved' ? 'badge-success' : 'badge-warning'}`}>
                          {item.decision}
                        </span>
                        {item.decision_at && <time>{formatDateTime(item.decision_at)}</time>}
                        {item.comments && <p>{item.comments}</p>}
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="request-history-empty">No approval history has been recorded.</p>
                )}
              </section>

              {detail.can_decide && (
                <section className="request-detail-section request-approver-actions">
                  <h3>Approver Actions</h3>
                  <label className="input-label" htmlFor="approval-comments">Comments (optional)</label>
                  <textarea
                    id="approval-comments"
                    className="input"
                    rows={3}
                    value={decisionComments}
                    onChange={(event) => setDecisionComments(event.target.value)}
                    disabled={savingDecision}
                  />
                  <div className="flex gap-8" style={{ marginTop: 12 }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleDecision('Approved')}
                      disabled={savingDecision}
                    >
                      <CheckCircle2 size={15} /> Approve
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleDecision('Rejected')}
                      disabled={savingDecision}
                    >
                      <XCircle size={15} /> Reject
                    </button>
                  </div>
                </section>
              )}
              {!detail.test_mode && !detail.can_decide && detail.status === 'Pending Approval' && (
                <div className="request-approval-readonly">
                  <AlertCircle size={16} />
                  Only the assigned, authenticated approver can decide this stage.
                </div>
              )}
            </>
          )}
        </div>
      </aside>
    </div>
  );
};

const LicenseRequestsPage = () => {
  const { user } = useAuth();
  const [licenses, setLicenses] = useState([]);
  const [users, setUsers] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [error, setError] = useState('');
  const [optionsError, setOptionsError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);

  const loadRequests = useCallback(async () => {
    setError('');
    try {
      const result = await getLicenseRequests();
      setRequests(Array.isArray(result.data) ? result.data : []);
    } catch (loadError) {
      console.error('Failed to load license requests:', loadError);
      setError(
        loadError.response?.data?.detail
          || 'Unable to load license requests. Verify your access and try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    getLicenseRequestOptions()
      .then((result) => {
        if (!active) return;
        setUsers(Array.isArray(result.data?.users) ? result.data.users : []);
        setLicenses(Array.isArray(result.data?.licenses) ? result.data.licenses : []);
      })
      .catch((optionsLoadError) => {
        console.error('Failed to load authenticated request options:', optionsLoadError);
        if (active) {
          setOptionsError(
            optionsLoadError.response?.data?.detail
              || 'Unable to load request options for the authenticated employee.'
          );
        }
      })
      .finally(() => {
        if (active) setOptionsLoading(false);
      });

    loadRequests();
    return () => {
      active = false;
    };
  }, [loadRequests]);

  const handleSavedRequest = (savedRequest) => {
    setRequests((current) => [
      savedRequest,
      ...current.filter((item) => item.request_id !== savedRequest.request_id),
    ]);
    setSuccessMessage(`Request ${savedRequest.request_id} was saved with status ${savedRequest.status}.`);
    loadRequests();
  };

  const handleDecisionSaved = (updatedRequest) => {
    setRequests((current) => current.map(
      (item) => item.request_id === updatedRequest.request_id ? updatedRequest : item
    ));
  };

  const requestRoles = user?.roles || [];
  const canRequest = user?.license_request_test_mode
    || requestRoles.includes('License.Requester')
    || requestRoles.includes('License.Admin');

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">License Requests</h1>
          <p className="page-desc">Submit and track application license requests in one place.</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setRequestModalOpen(true)}
          disabled={optionsLoading || !canRequest}
        >
          <Plus size={16} /> Request License
        </button>
      </div>

      {optionsError && <AlertBanner type="error" message={optionsError} />}
      {error && (
        <AlertBanner
          type="error"
          message={error}
          onDismiss={() => setError('')}
        />
      )}
      {successMessage && (
        <AlertBanner
          type="success"
          message={successMessage}
          onDismiss={() => setSuccessMessage('')}
        />
      )}

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>Request ID</th>
              <th>Employee</th>
              <th>Department</th>
              <th>Application</th>
              <th>License Type</th>
              <th>Requested Date</th>
              <th>Approver</th>
              <th>Request Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} style={{ padding: 24 }}><Spinner size={28} /></td></tr>
            ) : requests.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: 0 }}>
                  <EmptyState
                    icon={<FileText size={24} />}
                    title={error ? 'Requests could not be loaded' : 'No saved license requests'}
                    description={error ? 'Resolve the access or connection issue and retry.' : 'Submitted requests will appear here after the backend confirms they are saved.'}
                    action={error && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setLoading(true);
                          loadRequests();
                        }}
                      >
                        Retry
                      </button>
                    )}
                  />
                </td>
              </tr>
            ) : requests.map((request) => (
              <tr
                key={request.request_id}
                className="request-table-row"
                onClick={() => setSelectedRequest(request)}
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    setSelectedRequest(request);
                  }
                }}
              >
                <td><button className="request-id-link" onClick={() => setSelectedRequest(request)}>{request.request_id}</button></td>
                <td>{request.employee_name}<small>{request.employee_email}</small></td>
                <td>{request.department}</td>
                <td>{request.application}</td>
                <td>{request.license_type || request.license_name || '—'}</td>
                <td>{formatDateTime(request.requested_at)}</td>
                <td>{request.approver_name || 'Not assigned'}</td>
                <td><span className={`badge ${request.status === 'Rejected' ? 'badge-danger' : request.status === 'Approved' ? 'badge-success' : 'badge-warning'}`}>{request.status}</span></td>
                <td>
                  <button className="btn btn-secondary btn-sm" onClick={(event) => {
                    event.stopPropagation();
                    setSelectedRequest(request);
                  }}>
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {optionsLoading && <Spinner size={24} />}
      <RequestLicenseModal
        open={requestModalOpen}
        licenses={licenses}
        users={users}
        onClose={() => setRequestModalOpen(false)}
        onSubmitSuccess={handleSavedRequest}
        submitRequest={requestLicense}
      />
      {selectedRequest && (
        <RequestDetailsDrawer
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onDecision={handleDecisionSaved}
        />
      )}
    </>
  );
};

export default LicenseRequestsPage;
