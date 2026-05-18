import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer} from 'recharts';

const API = process.env.REACT_APP_API_URL;

function Dashboard({ token, onLogout }) {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [stats, setStats] = useState({ total: 0, pending: 0, flagged: 0, approved: 0 });
  const [claims, setClaims] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ patient_name: '', insurance_provider: '', medication: '', amount: '', rxcui: '' });
  const [error, setError] = useState('');
  const [aiExplanation, setAiExplanation] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [activePage, setActivePage] = useState('dashboard');
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [auditLog, setAuditLog] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [medicationResults, setMedicationResults] = useState([]);
  const [medicationLoading, setMedicationLoading] = useState(false);

  const filteredClaims = claims.filter(c => {
    const matchSearch = c.patient_name.toLowerCase().includes(search.toLowerCase()) ||
      c.medication.toLowerCase().includes(search.toLowerCase());
    const matchStatus = filterStatus === 'all' || c.status === filterStatus;
    return matchSearch && matchStatus;
  });

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = async () => {
    try {
      const [statsRes, claimsRes, auditRes] = await Promise.all([
        axios.get(`${API}/api/claims/stats`, { headers }),
        axios.get(`${API}/api/claims`, { headers }),
        axios.get(`${API}/api/audit`, { headers }),
      ]);
      setStats(statsRes.data);
      setClaims(claimsRes.data);
      setAuditLog(auditRes.data);

      // Build pie chart data from stats
      setChartData([
        { name: 'Approved', value: statsRes.data.approved,       color: '#10b981' },
        { name: 'Pending',  value: statsRes.data.pending,        color: '#f59e0b' },
        { name: 'Flagged',  value: statsRes.data.flagged_status, color: '#8b5cf6' },
        { name: 'Rejected', value: statsRes.data.rejected,       color: '#ef4444' },
      ]);

      // Build trend data from claims
      const last7 = [];
      for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const count = claimsRes.data.filter(c => {
          const claimDate = new Date(c.created_at);
          return claimDate.toDateString() === date.toDateString();
        }).length;
        last7.push({ date: dateStr, claims: count });
      }
      setTrendData(last7);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchData(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const query = form.medication.trim();
    if (query.length < 2) {
      setMedicationResults([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setMedicationLoading(true);
      try {
        const res = await axios.get(`${API}/api/medications/search`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { query },
        });
        setMedicationResults(res.data.results || []);
      } catch (err) {
        setMedicationResults([]);
      }
      setMedicationLoading(false);
    }, 250);

    return () => clearTimeout(timeoutId);
  }, [form.medication, token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await axios.post(`${API}/api/claims`, form, { headers });
      setForm({ patient_name: '', insurance_provider: '', medication: '', amount: '', rxcui: '' });
      setShowForm(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.message || 'Error submitting claim');
    }
  };

  const updateStatus = async (id, status) => {
    try {
      await axios.patch(`${API}/api/claims/${id}/status`, { status }, { headers });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const getAiExplanation = async (claim) => {
    setAiLoading(true);
    setAiExplanation('');
    try {
        const res = await axios.post(`${API}/api/ai/explain/${claim.id}`, {}, { headers });
        setAiExplanation(res.data.explanation);
    } catch (err) {
        setAiExplanation('Unable to generate explanation.');
    }
    setAiLoading(false);
  };

  const statusColor = (status) => {
    const colors = { pending: '#f59e0b', approved: '#10b981', rejected: '#ef4444', flagged: '#8b5cf6' };
    return colors[status] || '#666';
  };

  const renderMedicationSearch = () => (
    <div style={styles.medicationField}>
      <input placeholder="Medication" value={form.medication}
        onChange={e => setForm({...form, medication: e.target.value, rxcui: ''})} required />
      {(medicationLoading || medicationResults.length > 0) && (
        <div style={styles.medicationResults}>
          {medicationLoading && <div style={styles.medicationHint}>Searching RxNorm...</div>}
          {!medicationLoading && medicationResults.slice(0, 6).map(medication => (
            <button
              key={medication.rxcui || medication.name}
              type="button"
              style={styles.medicationOption}
              onClick={() => {
                setForm({...form, medication: medication.name, rxcui: medication.rxcui || ''});
                setMedicationResults([]);
              }}
            >
              <span style={styles.medicationName}>{medication.name}</span>
              {medication.rxcui && <span style={styles.medicationCode}>RxCUI {medication.rxcui}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div style={styles.container}>
      <div style={styles.sidebar}>
        <div style={styles.logo}>💊 RxFlow</div>
        <div style={styles.userInfo}>
          <div style={styles.avatar}>{user.name?.[0] || 'U'}</div>
          <div>
            <div style={styles.userName}>{user.name}</div>
            <div style={styles.userRole}>{user.role}</div>
          </div>
        </div>
        <nav style={styles.nav}>
          <div style={{...styles.navItem, background: activePage === 'dashboard' ? 'rgba(67,97,238,0.5)' : 'rgba(67,97,238,0.2)'}} onClick={() => setActivePage('dashboard')}>📊 Dashboard</div>
          <div style={{...styles.navItem, background: activePage === 'claims' ? 'rgba(67,97,238,0.5)' : 'rgba(67,97,238,0.2)'}} onClick={() => setActivePage('claims')}>📋 Claims</div>
          <div style={{...styles.navItem, background: activePage === 'audit' ? 'rgba(67,97,238,0.5)' : 'rgba(67,97,238,0.2)'}} onClick={() => setActivePage('audit')}>📁 Audit Log</div>
        </nav>
        <button onClick={onLogout} style={styles.logoutBtn}>🚪 Logout</button>
      </div>

      <div style={styles.main}>
        <div style={styles.header}>
          <h1 style={styles.headerTitle}>
            {activePage === 'dashboard' && 'ClaimTrack Dashboard'}
            {activePage === 'claims' && 'Claims Management'}
            {activePage === 'audit' && 'Audit Log'}
          </h1>
          {activePage !== 'audit' && (
            <button onClick={() => setShowForm(!showForm)} style={styles.addBtn}>+ New Claim</button>
          )}
        </div>

        {activePage === 'dashboard' && (
          <>
            <div style={styles.statsGrid}>
              {[
                { label: 'Total Claims', value: stats.total, color: '#4361ee', icon: '📋' },
                { label: 'Pending', value: stats.pending, color: '#f59e0b', icon: '⏳' },
                { label: 'Flagged', value: stats.flagged, color: '#ef4444', icon: '🚨' },
                { label: 'Approved', value: stats.approved, color: '#10b981', icon: '✅' },
              ].map((s) => (
                <div key={s.label} style={{...styles.statCard, borderTop: `4px solid ${s.color}`}}>
                  <div style={styles.statIcon}>{s.icon}</div>
                  <div style={{...styles.statValue, color: s.color}}>{s.value}</div>
                  <div style={styles.statLabel}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Charts */}
            <div style={styles.chartsGrid}>
              <div style={styles.chartCard}>
                <h3 style={styles.chartTitle}>Claims by Status</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={chartData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({name, value}) => `${name}: ${value}`}>
                      {chartData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div style={styles.chartCard}>
                <h3 style={styles.chartTitle}>Claims This Week</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={trendData}>
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="claims" fill="#4361ee" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {showForm && (
              <div style={styles.formCard}>
                <h3 style={styles.formTitle}>Submit New Claim</h3>
                {error && <div style={styles.error}>{error}</div>}
                <form onSubmit={handleSubmit} style={styles.form}>
                  <input placeholder="Patient Name" value={form.patient_name}
                    onChange={e => setForm({...form, patient_name: e.target.value})} required />
                  <input placeholder="Insurance Provider" value={form.insurance_provider}
                    onChange={e => setForm({...form, insurance_provider: e.target.value})} required />
                  {renderMedicationSearch()}
                  <input type="number" placeholder="Amount ($)" value={form.amount}
                    onChange={e => setForm({...form, amount: e.target.value})} required />
                  <div style={styles.formBtns}>
                    <button type="submit" style={styles.submitBtn}>Submit Claim</button>
                    <button type="button" onClick={() => setShowForm(false)} style={styles.cancelBtn}>Cancel</button>
                  </div>
                </form>
              </div>
            )}

            <div style={styles.tableCard}>
              <h3 style={styles.tableTitle}>Recent Claims</h3>
              <ClaimsTable claims={claims.slice(0,5)} onStatus={updateStatus} onExplain={getAiExplanation} statusColor={statusColor} styles={styles} />
              {(aiLoading || aiExplanation) && (
                <div style={styles.aiPanel}>
                  <h4 style={styles.aiTitle}>🤖 AI Anomaly Explanation</h4>
                  <p style={styles.aiText}>{aiLoading ? 'Generating Claude explanation...' : aiExplanation}</p>
                  {!aiLoading && <button onClick={() => setAiExplanation('')} style={styles.aiClose}>Dismiss</button>}
                </div>
              )}
            </div>
          </>
        )}

        {activePage === 'claims' && (
          <>
            {showForm && (
              <div style={styles.formCard}>
                <h3 style={styles.formTitle}>Submit New Claim</h3>
                {error && <div style={styles.error}>{error}</div>}
                <form onSubmit={handleSubmit} style={styles.form}>
                  <input placeholder="Patient Name" value={form.patient_name}
                    onChange={e => setForm({...form, patient_name: e.target.value})} required />
                  <input placeholder="Insurance Provider" value={form.insurance_provider}
                    onChange={e => setForm({...form, insurance_provider: e.target.value})} required />
                  {renderMedicationSearch()}
                  <input type="number" placeholder="Amount ($)" value={form.amount}
                    onChange={e => setForm({...form, amount: e.target.value})} required />
                  <div style={styles.formBtns}>
                    <button type="submit" style={styles.submitBtn}>Submit Claim</button>
                    <button type="button" onClick={() => setShowForm(false)} style={styles.cancelBtn}>Cancel</button>
                  </div>
                </form>
              </div>
            )}
            <div style={styles.tableCard}>
              <div style={styles.searchBar}>
                <input placeholder="🔍 Search by patient or medication..." value={search}
                  onChange={e => setSearch(e.target.value)} style={styles.searchInput} />
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={styles.filterSelect}>
                  <option value="all">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="flagged">Flagged</option>
                </select>
              </div>
              <ClaimsTable claims={filteredClaims} onStatus={updateStatus} onExplain={getAiExplanation} statusColor={statusColor} styles={styles} />
              {(aiLoading || aiExplanation) && (
                <div style={styles.aiPanel}>
                  <h4 style={styles.aiTitle}>🤖 AI Anomaly Explanation</h4>
                  <p style={styles.aiText}>{aiLoading ? 'Generating Claude explanation...' : aiExplanation}</p>
                  {!aiLoading && <button onClick={() => setAiExplanation('')} style={styles.aiClose}>Dismiss</button>}
                </div>
              )}
            </div>
          </>
        )}

        {activePage === 'audit' && (
          <div style={styles.tableCard}>
            <h3 style={styles.tableTitle}>Audit Log</h3>
            <table style={styles.table}>
              <thead>
                <tr style={styles.tableHeader}>
                  <th style={styles.th}>Time</th>
                  <th style={styles.th}>User</th>
                  <th style={styles.th}>Action</th>
                  <th style={styles.th}>Claim ID</th>
                </tr>
              </thead>
              <tbody>
                {auditLog.map(log => (
                  <tr key={log.id} style={styles.tableRow}>
                    <td style={styles.td}>{new Date(log.timestamp).toLocaleString()}</td>
                    <td style={styles.td}>{log.user_name || 'System'}</td>
                    <td style={styles.td}>{log.action}</td>
                    <td style={styles.td}>#{log.claim_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {auditLog.length === 0 && <p style={styles.empty}>No audit log entries yet.</p>}
          </div>
        )}
      </div>
    </div>
  );
}

function ClaimsTable({ claims, onStatus, onExplain, statusColor, styles }) {
  return (
    <table style={styles.table}>
      <thead>
        <tr style={styles.tableHeader}>
          <th style={styles.th}>Patient</th>
          <th style={styles.th}>Insurance</th>
          <th style={styles.th}>Medication</th>
          <th style={styles.th}>Amount</th>
          <th style={styles.th}>Status</th>
          <th style={styles.th}>Anomaly</th>
          <th style={styles.th}>Actions</th>
        </tr>
      </thead>
      <tbody>
        {claims.map((claim) => (
          <tr key={claim.id} style={styles.tableRow}>
            <td style={styles.td}>{claim.patient_name}</td>
            <td style={styles.td}>{claim.insurance_provider}</td>
            <td style={styles.td}>{claim.medication}</td>
            <td style={styles.td}>${parseFloat(claim.amount).toFixed(2)}</td>
            <td style={styles.td}>
              <span style={{...styles.badge, background: statusColor(claim.status)}}>{claim.status}</span>
            </td>
            <td style={styles.td}>
              {claim.anomaly_flag ? (
                <div>
                  <span style={styles.anomalyBadge}>⚠️ Flagged</span>
                  <button onClick={() => onExplain(claim)} style={styles.aiBtn}>🤖 Explain</button>
                </div>
              ) : (
                <span style={styles.okBadge}>✅ OK</span>
              )}
            </td>
            <td style={styles.td}>
              {claim.status === 'pending' ? (
                <div style={styles.actionBtns}>
                  <button onClick={() => onStatus(claim.id, 'approved')} style={styles.approveBtn}>✓</button>
                  <button onClick={() => onStatus(claim.id, 'rejected')} style={styles.rejectBtn}>✕</button>
                </div>
              ) : null}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const styles = {
  container: { display: 'flex', minHeight: '100vh' },
  sidebar: {
    width: '240px', background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)',
    color: 'white', padding: '24px', display: 'flex', flexDirection: 'column', position: 'fixed', height: '100vh'
  },
  logo: { fontSize: '32px', fontWeight: '900', marginBottom: '32px', color: 'white', letterSpacing: '-1px', textShadow: '0 0 20px rgba(67,97,238,0.8)' },  userInfo: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px' },
  avatar: { width: '40px', height: '40px', borderRadius: '50%', background: '#4361ee', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '700', fontSize: '18px' },
  userName: { fontWeight: '600', fontSize: '14px' },
  userRole: { fontSize: '12px', color: '#94a3b8', textTransform: 'capitalize' },
  nav: { flex: 1 },
  navItem: { padding: '12px 16px', borderRadius: '8px', cursor: 'pointer', fontSize: '14px', background: 'rgba(67,97,238,0.2)', marginBottom: '8px', color: 'white', fontWeight: '500', transition: 'all 0.2s' },  logoutBtn: { background: 'rgba(239,68,68,0.2)', color: '#fca5a5', width: '100%', padding: '10px', borderRadius: '8px' },
  main: { marginLeft: '240px', flex: 1, padding: '32px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
  headerTitle: { fontSize: '28px', fontWeight: '800', color: '#1a1a2e' },
  addBtn: { background: 'linear-gradient(135deg, #4361ee, #3a0ca3)', color: 'white', padding: '12px 24px', borderRadius: '8px', fontSize: '14px' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' },
  statCard: { background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' },
  statIcon: { fontSize: '24px', marginBottom: '8px' },
  statValue: { fontSize: '32px', fontWeight: '800', lineHeight: 1 },
  statLabel: { fontSize: '13px', color: '#666', marginTop: '4px' },
  formCard: { background: 'white', borderRadius: '12px', padding: '24px', marginBottom: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' },
  formTitle: { fontSize: '18px', fontWeight: '700', marginBottom: '16px' },
  form: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' },
  formBtns: { gridColumn: 'span 2', display: 'flex', gap: '12px' },
  submitBtn: { background: 'linear-gradient(135deg, #4361ee, #3a0ca3)', color: 'white', padding: '10px 24px' },
  cancelBtn: { background: '#f1f5f9', color: '#64748b', padding: '10px 24px' },
  error: { background: '#fee2e2', color: '#dc2626', padding: '10px', borderRadius: '6px', marginBottom: '16px', fontSize: '14px', gridColumn: 'span 2' },
  tableCard: { background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' },
  tableTitle: { fontSize: '18px', fontWeight: '700', marginBottom: '16px' },
  table: { width: '100%', borderCollapse: 'collapse' },
  tableHeader: { background: '#f8fafc' },
  th: { padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', borderBottom: '1px solid #e2e8f0' },
  tableRow: { borderBottom: '1px solid #f1f5f9' },
  td: { padding: '14px 16px', fontSize: '14px' },
  badge: { color: 'white', padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: '600' },
  anomalyBadge: { color: '#dc2626', fontSize: '12px', fontWeight: '600' },
  okBadge: { color: '#10b981', fontSize: '12px', fontWeight: '600' },
  actionBtns: { display: 'flex', gap: '8px' },
  approveBtn: { background: '#dcfce7', color: '#16a34a', padding: '4px 10px', borderRadius: '6px', fontWeight: '700' },
  rejectBtn: { background: '#fee2e2', color: '#dc2626', padding: '4px 10px', borderRadius: '6px', fontWeight: '700' },
  empty: { textAlign: 'center', color: '#94a3b8', padding: '40px', fontSize: '14px' },
  aiBtn: { background: '#ede9fe', color: '#7c3aed', padding: '3px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', marginLeft: '8px', cursor: 'pointer' },
  aiPanel: { marginTop: '20px', background: 'linear-gradient(135deg, #ede9fe, #ddd6fe)', borderRadius: '12px', padding: '20px', border: '1px solid #c4b5fd' },
  aiTitle: { fontSize: '16px', fontWeight: '700', color: '#5b21b6', marginBottom: '8px' },
  aiText: { fontSize: '14px', color: '#4c1d95', lineHeight: '1.6' },
  aiClose: { marginTop: '12px', background: '#7c3aed', color: 'white', padding: '6px 16px', borderRadius: '6px', fontSize: '13px' },
  searchBar: { display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' },
  searchInput: { flex: 1, minWidth: '220px', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: '14px' },
  filterSelect: { width: '180px', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: '14px' },
  chartsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' },
  chartCard: { background: 'white', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' },
  chartTitle: { fontSize: '16px', fontWeight: '700', marginBottom: '16px', color: '#1a1a2e' },
  medicationField: { position: 'relative' },
  medicationResults: {
    position: 'absolute', top: '46px', left: 0, right: 0, background: 'white', border: '1px solid #e2e8f0',
    borderRadius: '10px', boxShadow: '0 12px 30px rgba(15,23,42,0.16)', zIndex: 20, overflow: 'hidden'
  },
  medicationHint: { padding: '12px 14px', color: '#64748b', fontSize: '13px' },
  medicationOption: {
    width: '100%', display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center',
    padding: '10px 12px', background: 'white', color: '#0f172a', borderRadius: 0, borderBottom: '1px solid #f1f5f9',
    textAlign: 'left', cursor: 'pointer'
  },
  medicationName: { fontSize: '13px', fontWeight: '600' },
  medicationCode: { fontSize: '11px', color: '#64748b', whiteSpace: 'nowrap' }
};

export default Dashboard;
