import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/store';
import { healthAPI, doctorAPI } from '../services/api';

/* ── Brand shield SVG ─────────────────────────────────────────────────────── */
const ShieldIcon = () => (
  <svg viewBox="0 0 32 32" fill="none" className="w-8 h-8 flex-shrink-0">
    <path
      d="M16 2L4 7v9c0 7.18 5.14 13.9 12 15.48C22.86 29.9 28 23.18 28 16V7L16 2z"
      fill="url(#sg)"
    />
    <path d="M11 16.5l3 3 7-7" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    <defs>
      <linearGradient id="sg" x1="4" y1="2" x2="28" y2="31" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#2dd4bf" />
        <stop offset="100%" stopColor="#0a2342" />
      </linearGradient>
    </defs>
  </svg>
);

/* ── Nav link definitions ─────────────────────────────────────────────────── */
const NAV_PATIENT = [
  { to: '/analysis',     label: 'Upload',       icon: '📤' },
  { to: '/health-history', label: 'History',    icon: '📋' },
  { to: '/patient-chat', label: 'Chat',         icon: '💬' },
];
const NAV_DOCTOR = [
  { to: '/doctor-dashboard', label: 'Portal',  icon: '🏥' },
];
const EXTRA_PATIENT = (patientId) => [
  { to: `/medications/${patientId}`,     label: 'Medications', icon: '💊' },
  { to: `/fitness-tracking/${patientId}`, label: 'Fitness',   icon: '📱' },
  { to: `/health-chatbot/${patientId}`,  label: 'AI Assistant', icon: '🤖' },
  { to: '/appointments',                 label: 'Appointments', icon: '📅' },
];

/* ── Bell SVG ─────────────────────────────────────────────────────────────── */
const BellIcon = () => (
  <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
);

/* ── Logout SVG ───────────────────────────────────────────────────────────── */
const LogoutIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

/* ════════════════════════════════════════════════════════════════════════════ */
export default function Navbar() {
  const { user, role, clearAuth } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const notifRef = useRef(null);

  const [menuOpen, setMenuOpen]           = useState(false);
  const [unreadCount, setUnreadCount]     = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showNotifs, setShowNotifs]       = useState(false);

  const patientId = user?.id || user?._id || user?.user_id;
  const doctorId  = user?.id || user?._id || user?.user_id;

  /* ── Close notif dropdown on outside click ── */
  useEffect(() => {
    const handler = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifs(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  /* ── Load notifications ── */
  useEffect(() => {
    if (!user) return;
    const load = async () => {
      try {
        if (role === 'patient' && patientId) {
          const res = await healthAPI.getNotifications(patientId);
          const items = res.data.notifications || [];
          setUnreadCount(items.filter(n => !n.is_read).length);
          setNotifications(items.map(n => ({
            id: n._id,
            title: n.title || n.category,
            text: n.message || n.title,
            icon: n.category === 'sos' ? '🆘' : n.category === 'chat' ? '💬' : n.category === 'medication' ? '💊' : '📅',
          })));
        } else if (role === 'doctor' && doctorId) {
          const res = await doctorAPI.getNotifications();
          const items = res.data.notifications || [];
          setUnreadCount(items.filter(n => !n.is_read).length);
          setNotifications(items.map(n => ({
            id: n._id,
            title: n.title || n.category,
            text: n.message || n.title,
            icon: n.category === 'chat' ? '💬' : '📅',
          })));
        }
      } catch { /* silently skip */ }
    };
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [user, role, patientId, doctorId]);

  /* ── Helpers ── */
  const handleLogout = () => {
    clearAuth();
    navigate('/login');
    setMenuOpen(false);
  };

  const handleNotifClick = async () => {
    setShowNotifs(false);
    try {
      if (role === 'patient' && patientId) await healthAPI.markNotificationsRead(patientId);
      if (role === 'doctor') await doctorAPI.markNotificationsRead();
      setUnreadCount(0);
    } catch { /* ignore */ }
    navigate(role === 'doctor' ? '/doctor-dashboard' : '/patient-chat');
  };

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + '/');

  const allLinks = role === 'doctor'
    ? NAV_DOCTOR
    : [...NAV_PATIENT, ...(patientId ? EXTRA_PATIENT(patientId) : [])];

  /* ── Avatar initial ── */
  const initial = (user?.first_name || user?.email || 'U')[0].toUpperCase();
  const displayName = role === 'doctor'
    ? `Dr. ${user?.last_name || user?.email || ''}`
    : (user?.first_name || user?.email || '');

  /* ════════════════════════════════════════════════════════════════════════ */
  return (
    <nav className="sticky top-0 z-50 bg-[#0a2342] border-b border-white/10 shadow-xl shadow-black/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-[60px] gap-4">

          {/* ── Logo ── */}
          <Link
            to="/"
            onClick={() => setMenuOpen(false)}
            className="flex items-center gap-2.5 flex-shrink-0 group"
          >
            <ShieldIcon />
            <div className="flex items-baseline gap-1 leading-none">
              <span className="text-white font-black text-[17px] tracking-tight">MEDO</span>
              <span className="text-teal-400 font-black text-[17px] tracking-tight">SHIELD</span>
              <span className="text-white/40 text-[11px] font-semibold tracking-widest ml-0.5">AI</span>
            </div>
          </Link>

          {/* ── Desktop Nav Links ── */}
          {user && (
            <div className="hidden lg:flex items-center gap-0.5 flex-1 justify-center">
              {allLinks.map(link => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[13px] font-semibold transition-all duration-200 ${
                    isActive(link.to)
                      ? 'bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/30'
                      : 'text-white/60 hover:text-white hover:bg-white/8'
                  }`}
                >
                  <span className="text-[13px] leading-none">{link.icon}</span>
                  {link.label}
                </Link>
              ))}
            </div>
          )}

          {/* ── Right Side ── */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {user ? (
              <>
                {/* Notification Bell */}
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={() => setShowNotifs(v => !v)}
                    className="relative w-9 h-9 flex items-center justify-center rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
                    title="Notifications"
                  >
                    <BellIcon />
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-0.5 leading-none">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>

                  {/* Dropdown */}
                  {showNotifs && (
                    <div className="absolute top-[calc(100%+8px)] right-0 w-80 bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden z-50">
                      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50">
                        <span className="font-bold text-slate-800 text-sm">Notifications</span>
                        {unreadCount > 0 && (
                          <span className="text-xs bg-red-100 text-red-600 font-bold px-2 py-0.5 rounded-full">
                            {unreadCount} new
                          </span>
                        )}
                      </div>
                      {notifications.length === 0 ? (
                        <div className="py-8 text-center text-slate-400 text-sm">✓ All caught up!</div>
                      ) : (
                        <div className="max-h-72 overflow-y-auto divide-y divide-slate-50">
                          {notifications.slice(0, 8).map(n => (
                            <button
                              key={n.id}
                              onClick={handleNotifClick}
                              className="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex gap-3 items-start"
                            >
                              <span className="text-xl flex-shrink-0 mt-0.5">{n.icon}</span>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-bold text-slate-700 truncate">{n.title}</p>
                                <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{n.text}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* User Badge */}
                <div className="hidden md:flex items-center gap-2 bg-white/8 hover:bg-white/12 rounded-xl px-3 py-1.5 transition-all cursor-default">
                  <div className="w-6 h-6 rounded-full bg-teal-500 flex items-center justify-center flex-shrink-0">
                    <span className="text-[11px] font-bold text-white">{initial}</span>
                  </div>
                  <span className="text-[13px] text-white/90 font-semibold max-w-[100px] truncate">
                    {displayName}
                  </span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                    role === 'doctor'
                      ? 'bg-teal-500/20 text-teal-300'
                      : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {role}
                  </span>
                </div>

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="hidden md:flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-white/8 hover:bg-white/15 text-white/70 hover:text-white text-[13px] font-semibold transition-all"
                >
                  <LogoutIcon />
                  Logout
                </button>
              </>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/login"
                  className="text-white/70 hover:text-white text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-white/10 transition-all">
                  Patient Login
                </Link>
                <Link to="/doctor-login"
                  className="text-white/70 hover:text-white text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-white/10 transition-all">
                  Doctor Login
                </Link>
                <Link to="/register"
                  className="px-4 py-1.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-white text-sm font-bold transition-all shadow-sm">
                  Get Started
                </Link>
              </div>
            )}

            {/* Hamburger */}
            <button
              onClick={() => setMenuOpen(v => !v)}
              className="lg:hidden w-9 h-9 flex flex-col items-center justify-center gap-1.5 rounded-xl hover:bg-white/10 transition-colors"
              aria-label="Toggle menu"
            >
              <span className={`block w-5 h-[2px] bg-white rounded-full transition-all duration-300 origin-center ${menuOpen ? 'rotate-45 translate-y-[7px]' : ''}`} />
              <span className={`block w-5 h-[2px] bg-white rounded-full transition-all duration-300 ${menuOpen ? 'opacity-0 scale-x-0' : ''}`} />
              <span className={`block w-5 h-[2px] bg-white rounded-full transition-all duration-300 origin-center ${menuOpen ? '-rotate-45 -translate-y-[7px]' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* ── Mobile Menu ── */}
      <div
        className={`lg:hidden overflow-hidden transition-all duration-300 ease-in-out ${
          menuOpen ? 'max-h-[600px] border-t border-white/10' : 'max-h-0'
        }`}
      >
        <div className="bg-[#0a2342] px-4 pt-3 pb-5 space-y-1">
          {user ? (
            <>
              {/* User info strip */}
              <div className="flex items-center gap-3 px-3 py-3 mb-2 bg-white/5 rounded-xl">
                <div className="w-9 h-9 rounded-full bg-teal-500 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-white">{initial}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-bold truncate">{displayName}</p>
                  <p className="text-white/40 text-xs capitalize">{role}</p>
                </div>
                {unreadCount > 0 && (
                  <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                    {unreadCount} new
                  </span>
                )}
              </div>

              {/* Nav links */}
              {allLinks.map(link => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    isActive(link.to)
                      ? 'bg-teal-500/20 text-teal-300'
                      : 'text-white/70 hover:text-white hover:bg-white/8'
                  }`}
                >
                  <span className="text-base">{link.icon}</span>
                  {link.label}
                </Link>
              ))}

              <div className="pt-3 mt-2 border-t border-white/10">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold text-white/70 hover:text-white hover:bg-white/10 transition-all"
                >
                  <LogoutIcon />
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login"        onClick={() => setMenuOpen(false)} className="block px-4 py-3 rounded-xl text-white/80 hover:text-white hover:bg-white/10 text-sm font-medium">Patient Login</Link>
              <Link to="/doctor-login" onClick={() => setMenuOpen(false)} className="block px-4 py-3 rounded-xl text-white/80 hover:text-white hover:bg-white/10 text-sm font-medium">Doctor Login</Link>
              <Link to="/register"     onClick={() => setMenuOpen(false)} className="block px-4 py-3 rounded-xl bg-teal-500 text-white text-sm font-bold text-center mt-2">Get Started</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
