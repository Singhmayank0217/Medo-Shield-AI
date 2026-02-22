import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/store';
import { patientAPI, healthAPI } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const StatCard = ({ title, value, sub, color, icon }) => (
  <motion.div whileHover={{ y: -2 }} className="medo-card p-5">
    <div className="flex items-start justify-between mb-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${color}`}>
        {icon}
      </div>
    </div>
    <p className="text-2xl font-bold text-slate-800">{value}</p>
    <p className="text-sm font-medium text-slate-500 mt-0.5">{title}</p>
    {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
  </motion.div>
);

// ─── SOS Alert Modal ───────────────────────────────────────────────────────────
function SOSModal({ onConfirm, onCancel, sending }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        transition={{ type: 'spring', duration: 0.4 }}
        className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full relative overflow-hidden"
      >
        {/* Red glow top */}
        <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-red-500/20 blur-2xl pointer-events-none" />

        <div className="flex flex-col items-center text-center">
          {/* Pulsing SOS icon */}
          <div className="relative mb-5">
            <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center">
              <span className="text-4xl">🆘</span>
            </div>
            <span className="absolute inset-0 rounded-full border-4 border-red-400 animate-ping opacity-40" />
          </div>

          <h2 className="text-2xl font-bold text-slate-800 mb-2">Send Emergency Alert?</h2>
          <p className="text-slate-500 text-sm leading-relaxed mb-1">
            This will immediately send an SMS to
          </p>
          <p className="text-red-600 font-bold text-lg mb-3">+91 9330736637</p>
          <p className="text-slate-500 text-sm mb-6">
            The message will include your <strong>name</strong>, <strong>current GPS location</strong>, and a <strong>Google Maps link</strong>.
          </p>

          <div className="flex gap-3 w-full">
            <button
              onClick={onCancel}
              disabled={sending}
              className="flex-1 px-5 py-3 rounded-xl border border-slate-200 text-slate-600 font-semibold hover:bg-slate-50 transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={sending}
              className="flex-1 px-5 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-all disabled:opacity-70 flex items-center justify-center gap-2"
            >
              {sending ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Sending…
                </>
              ) : (
                <>🚨 Send Alert</>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── SOS Result Banner ─────────────────────────────────────────────────────────
function SOSResult({ result, onClose }) {
  const success = result?.sms_sent;
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`rounded-2xl p-5 flex items-start gap-4 border ${
        success
          ? 'bg-green-50 border-green-200'
          : 'bg-amber-50 border-amber-200'
      }`}
    >
      <span className="text-2xl flex-shrink-0">{success ? '✅' : '⚠️'}</span>
      <div className="flex-1">
        <p className={`font-bold text-sm mb-1 ${success ? 'text-green-700' : 'text-amber-700'}`}>
          {success ? 'SOS Alert Sent Successfully!' : 'Alert Logged — SMS Delivery Issue'}
        </p>
        <p className={`text-xs leading-relaxed ${success ? 'text-green-600' : 'text-amber-600'}`}>
          {result?.message}
        </p>
        {result?.maps_link && (
          <a
            href={result.maps_link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2"
          >
            📍 View your shared location
          </a>
        )}
      </div>
      <button onClick={onClose} className="text-slate-400 hover:text-slate-600 ml-2 text-lg leading-none">✕</button>
    </motion.div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [dashData, setDashData] = useState(null);
  const [trends, setTrends] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // SOS state
  const [showSOSModal, setShowSOSModal] = useState(false);
  const [sosSending, setSosSending] = useState(false);
  const [sosResult, setSosResult] = useState(null);

  const patientId = user?.id || user?._id || user?.user_id;

  const loadData = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError('');
    try {
      const [dashRes, trendsRes, notifRes] = await Promise.allSettled([
        patientAPI.getDashboard(),
        patientAPI.getTrends(30),
        healthAPI.getNotifications(patientId),
      ]);
      if (dashRes.status === 'fulfilled')   setDashData(dashRes.value.data);
      if (trendsRes.status === 'fulfilled') setTrends(trendsRes.value.data.trends || []);
      if (notifRes.status === 'fulfilled')  setNotifications(notifRes.value.data.notifications || []);
    } catch (err) {
      setError('Failed to load dashboard data. Please refresh.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => { loadData(); }, [loadData]);

  // ─── SOS Handlers ────────────────────────────────────────────────────────────
  const handleSOSClick = () => {
    setSosResult(null);
    setShowSOSModal(true);
  };

  const handleSOSConfirm = () => {
    setSosSending(true);

    const sendAlert = async (lat, lng, locationName) => {
      try {
        const payload = {
          latitude: lat ?? null,
          longitude: lng ?? null,
          location_name: locationName || null,
          message: null,
        };
        const res = await healthAPI.sendSOSAlert(payload);
        setSosResult(res.data);
      } catch (err) {
        setSosResult({
          sms_sent: false,
          message: err?.response?.data?.detail || 'Failed to send alert. Please call emergency services directly.',
        });
      } finally {
        setSosSending(false);
        setShowSOSModal(false);
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          sendAlert(latitude, longitude, null);
        },
        (geoErr) => {
          console.warn('Geolocation denied or failed:', geoErr.message);
          sendAlert(null, null, 'Location unavailable');
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    } else {
      sendAlert(null, null, 'Geolocation not supported');
    }
  };

  const handleSOSCancel = () => {
    if (!sosSending) setShowSOSModal(false);
  };

  // ─── Render ──────────────────────────────────────────────────────────────────
  const profile = dashData?.profile || user || {};
  const stats = dashData?.stats || {};
  const recentReports = dashData?.recent_reports || [];
  const medications = dashData?.medications || [];

  const quickActions = [
    { label: 'Upload Report', icon: '📄', path: '/analysis', color: 'bg-primary' },
    { label: 'Medications', icon: '💊', path: `/medications/${patientId}`, color: 'bg-secondary' },
    { label: 'AI Assistant', icon: '🤖', path: `/health-chatbot/${patientId}`, color: 'bg-purple-600' },
    { label: 'Timeline', icon: '📊', path: `/health-timeline/${patientId}`, color: 'bg-amber-500' },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-secondary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* ── SOS Modal (portal-like, rendered via AnimatePresence) ── */}
      <AnimatePresence>
        {showSOSModal && (
          <SOSModal
            onConfirm={handleSOSConfirm}
            onCancel={handleSOSCancel}
            sending={sosSending}
          />
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="page-header">
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="text-white/60 text-sm font-medium uppercase tracking-wider mb-1">Patient Dashboard</p>
              <h1 className="text-3xl font-bold text-white">
                Welcome back, {profile.first_name || 'Patient'}
              </h1>
              <p className="text-white/60 text-sm mt-1">
                {profile.email} &nbsp;·&nbsp; {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <div className="flex items-center gap-3 self-start sm:self-auto">
              {/* 🚨 SOS Alert Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSOSClick}
                className="relative flex items-center gap-2 px-5 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-bold transition-all shadow-lg shadow-red-500/40"
                title="Send SOS Emergency Alert"
              >
                {/* Pulse ring */}
                <span className="absolute inset-0 rounded-xl border-2 border-red-300 animate-ping opacity-40 pointer-events-none" />
                <span className="text-base">🆘</span>
                SOS Alert
              </motion.button>

              {/* Refresh */}
              <button onClick={loadData} className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-semibold transition-all">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {error && <div className="alert-error">{error}</div>}

        {/* SOS Result Banner */}
        <AnimatePresence>
          {sosResult && (
            <SOSResult result={sosResult} onClose={() => setSosResult(null)} />
          )}
        </AnimatePresence>

        {/* ── SOS Emergency Card ── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl overflow-hidden border border-red-200 bg-gradient-to-r from-red-50 to-rose-50"
        >
          <div className="p-5 flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3 flex-1">
              <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center text-2xl flex-shrink-0">
                🆘
              </div>
              <div>
                <p className="font-bold text-slate-800 text-sm">Emergency SOS Alert</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  One tap sends your <strong>name</strong>, <strong>GPS location</strong> & Google Maps link to <strong>+91 9330736637</strong>
                </p>
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleSOSClick}
              className="relative flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-sm transition-all shadow-md shadow-red-300 flex-shrink-0"
            >
              <span className="absolute inset-0 rounded-xl border-2 border-red-400 animate-ping opacity-30 pointer-events-none" />
              🚨 Send SOS Now
            </motion.button>
          </div>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Total Reports"     value={stats.total_sessions || 0}      icon="📋" color="bg-blue-50 text-blue-600"   sub="All time" />
          <StatCard title="AI Analyses"       value={stats.total_analyses || 0}      icon="🤖" color="bg-teal-50 text-teal-600"   sub="Gemini processed" />
          <StatCard title="Active Meds"       value={medications.length || 0}        icon="💊" color="bg-purple-50 text-purple-600" sub="Scheduled today" />
          <StatCard title="Notifications"     value={notifications.filter(n => !n.read).length} icon="🔔" color="bg-amber-50 text-amber-600" sub="Unread" />
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-lg font-bold text-slate-800 mb-3">Quick Actions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {quickActions.map(a => (
              <motion.button
                key={a.label}
                whileHover={{ y: -2, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate(a.path)}
                className={`flex flex-col items-center gap-2 py-5 rounded-2xl text-white font-semibold text-sm transition-all ${a.color} shadow-sm hover:shadow-md`}
              >
                <span className="text-2xl">{a.icon}</span>
                {a.label}
              </motion.button>
            ))}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Trends Chart */}
          <div className="lg:col-span-2 medo-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-800">Health Trends (30 days)</h2>
              <button onClick={() => navigate(`/health-timeline/${patientId}`)}
                className="text-secondary text-sm font-semibold hover:underline">View All</button>
            </div>
            {trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={trends} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gaitGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#0d9488" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#0d9488" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="bradyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickFormatter={d => new Date(d).toLocaleDateString('en', { month: 'short', day: 'numeric' })} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', fontSize: 12 }}
                    labelFormatter={l => new Date(l).toLocaleDateString('en', { month: 'long', day: 'numeric' })}
                  />
                  <Area type="monotone" dataKey="gait_symmetry"    name="Gait Symmetry"    stroke="#0d9488" fill="url(#gaitGrad)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="bradykinesia_score" name="Bradykinesia"    stroke="#8b5cf6" fill="url(#bradyGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <div className="text-4xl mb-3">📈</div>
                <p className="text-slate-600 font-medium">No trend data yet</p>
                <p className="text-slate-400 text-sm mt-1">Upload a video or report to start tracking</p>
                <button onClick={() => navigate('/analysis')} className="btn-teal text-xs px-4 py-2 mt-4">
                  Upload Now
                </button>
              </div>
            )}
          </div>

          {/* Notifications */}
          <div className="medo-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800">Notifications</h2>
              {notifications.some(n => !n.read) && (
                <span className="badge-danger">{notifications.filter(n => !n.read).length} new</span>
              )}
            </div>
            {notifications.length === 0 ? (
              <div className="text-center py-10">
                <div className="text-3xl mb-2">🔔</div>
                <p className="text-slate-500 text-sm">No notifications</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {notifications.slice(0, 8).map((n, i) => (
                  <div key={i} className={`p-3 rounded-xl border text-sm ${
                    n.type === 'sos' || n.category === 'sos'
                      ? 'bg-red-50 border-red-100 text-red-700'
                      : n.type === 'high_risk' || n.priority === 'high'
                      ? 'bg-red-50 border-red-100 text-red-700'
                      : n.type === 'medication'
                      ? 'bg-purple-50 border-purple-100 text-purple-700'
                      : 'bg-blue-50 border-blue-100 text-blue-700'
                  }`}>
                    <p className="font-semibold">{n.title || n.type?.replace('_', ' ')}</p>
                    <p className="text-xs mt-0.5 opacity-80">{n.message || n.content}</p>
                    {n.created_at && <p className="text-xs mt-1 opacity-60">{new Date(n.created_at).toLocaleString()}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Reports */}
        <div className="medo-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-slate-800">Recent Reports &amp; Analyses</h2>
            <button onClick={() => navigate('/health-history')} className="text-secondary text-sm font-semibold hover:underline">View All</button>
          </div>
          {recentReports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="text-4xl mb-3">📭</div>
              <p className="text-slate-600 font-medium">No reports yet</p>
              <p className="text-slate-400 text-sm mt-1">Upload a PDF report or video to get started</p>
              <button onClick={() => navigate('/analysis')} className="btn-teal text-sm px-6 py-2.5 mt-4">
                Upload First Report
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full medo-table">
                <thead>
                  <tr>
                    <th>Report</th>
                    <th>Type</th>
                    <th>Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentReports.slice(0, 6).map((r, i) => (
                    <tr key={i}>
                      <td className="font-semibold text-slate-800">{r.title || r.file_name || `Report ${i + 1}`}</td>
                      <td>
                        <span className="badge-info capitalize">{(r.type || 'report').replace('_', ' ')}</span>
                      </td>
                      <td className="text-slate-500">{new Date(r.created_at).toLocaleDateString()}</td>
                      <td>
                        <span className={r.status === 'completed' ? 'badge-success' : 'badge-warning'}>
                          {r.status || 'completed'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Medication Reminders */}
        {medications.length > 0 && (
          <div className="medo-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800">Today's Medications</h2>
              <button onClick={() => navigate(`/medications/${patientId}`)} className="text-secondary text-sm font-semibold hover:underline">Manage</button>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {medications.slice(0, 6).map((med, i) => (
                <div key={i} className="flex items-center gap-3 p-4 bg-purple-50 border border-purple-100 rounded-xl">
                  <div className="w-9 h-9 rounded-lg bg-purple-100 flex items-center justify-center text-xl">💊</div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-800 text-sm truncate">{med.name || med.medication_name}</p>
                    <p className="text-xs text-slate-500">{med.dosage} · {med.frequency}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
