import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle2, XCircle, Clock3 } from 'lucide-react';
import { AlertBanner, Spinner } from '../components/ui';

const rawBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const apiBase = rawBase.endsWith('/v1') ? rawBase.slice(0, -3) : rawBase;

const ApprovalPage = () => {
  const { token } = useParams();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [comments, setComments] = useState('');
  const [busy, setBusy] = useState(null);
  const [done, setDone] = useState(null);

  useEffect(() => {
    let active = true;
    fetch(`${apiBase}/v1/approvals/preview?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || 'This approval link is invalid.');
        return data;
      })
      .then((data) => { if (active) setDetail(data); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token]);

  const decide = async (path, label) => {
    setBusy(label);
    setError('');
    try {
      const url = `${apiBase}/v1/approvals/${path}?token=${encodeURIComponent(token)}`
        + (comments.trim() ? `&comments=${encodeURIComponent(comments.trim())}` : '');
      const res = await fetch(url);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Decision failed.');
      setDone({ status: data.status, message: data.message });
      setDetail((prev) => (prev ? { ...prev, status: data.status } : prev));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  const rows = detail ? [
    ['Request ID', detail.request_id],
    ['Application', detail.application],
    ['License / Product', detail.license_label],
    ['License Type', detail.license_type || 'Business'],
    ['Request Type', 'New License'],
    ['Quantity', '1'],
    ['Priority', detail.urgency === 'Standard' ? 'Normal' : detail.urgency],
    ['Requested For', detail.employee_email ? `${detail.employee_name} (${detail.employee_email})` : detail.employee_name],
    ['Department', detail.department],
    ['Justification', detail.justification],
    ['Submitted At', detail.submitted_at ? new Date(detail.submitted_at).toLocaleString() : '-'],
    ['Status', detail.status],
  ] : [];

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9', display: 'flex', justifyContent: 'center', padding: '32px 16px' }}>
      <div style={{ width: '100%', maxWidth: 640, background: '#fff', borderRadius: 12, padding: 28, alignSelf: 'flex-start' }}>
        <p style={{ color: '#93c5fd', fontSize: 13, marginBottom: 16 }}>You are approving as: Tower Head</p>
        {loading && <Spinner size={28} />}
        {error && <AlertBanner type="error" message={error} />}
        {detail && (
          <table style={{ width: '100%', border: '1px solid #e2e8f0', borderCollapse: 'collapse', marginBottom: 18 }}>
            <tbody>
              {rows.map(([k, v]) => (
                <tr key={k}>
                  <td style={{ padding: '8px 12px', color: '#64748b', fontSize: 13, width: '38%' }}>{k}</td>
                  <td style={{ padding: '8px 12px', color: '#0f172a', fontSize: 13, fontWeight: 500 }}>{v || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {detail && done && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            {done.status === 'Approved'
              ? <CheckCircle2 size={40} color="#16a34a" />
              : <XCircle size={40} color="#dc2626" />}
            <p style={{ fontWeight: 600, marginTop: 8 }}>{done.message}</p>
            <p style={{ fontSize: 13, color: '#64748b' }}>Reflected in the License Requests portal.</p>
          </div>
        )}
        {detail && !done && detail.status !== 'Pending Approval' && (
          <div style={{ textAlign: 'center' }}>
            <Clock3 size={36} color="#64748b" />
            <p style={{ fontWeight: 600 }}>Already {String(detail.status || '').toLowerCase()}.</p>
          </div>
        )}
        {detail && !done && detail.status === 'Pending Approval' && (
          <>
            <label style={{ fontSize: 13, fontWeight: 600 }}>Comments (optional)</label>
            <textarea className="input" rows={3} value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Add a note for the requester..."
              style={{ width: '100%', margin: '6px 0 16px' }} />
            <div style={{ display: 'flex', gap: 14, justifyContent: 'center' }}>
              <button disabled={!!busy} onClick={() => decide('approve', 'Approve')}
                style={{ background: '#16a34a', color: '#fff', fontWeight: 700, padding: '12px 34px', borderRadius: 8, border: 'none' }}>
                {busy === 'Approve' ? 'Approving...' : 'Approve'}
              </button>
              <button disabled={!!busy} onClick={() => decide('decline', 'Decline')}
                style={{ background: '#dc2626', color: '#fff', fontWeight: 700, padding: '12px 34px', borderRadius: 8, border: 'none' }}>
                {busy === 'Decline' ? 'Declining...' : 'Decline'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ApprovalPage;
