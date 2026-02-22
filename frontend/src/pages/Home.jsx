import React from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../store/store";

const FLOW_STEPS = [
  {
    step: "01",
    color: "from-blue-500 to-primary",
    icon: (
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
        />
      </svg>
    ),
    title: "Authentication",
    subtitle: "Secure multi-role gateway",
    items: [
      "Patient & Doctor register/login",
      "JWT role-based access",
      "Dashboard access granted",
    ],
  },
  {
    step: "02",
    color: "from-teal-500 to-secondary",
    icon: (
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
    ),
    title: "Health Data Upload",
    subtitle: "PDF reports, symptoms, videos",
    items: [
      "Upload PDF medical reports",
      "Add symptom queries & history",
      "Secure cloud + DB storage",
    ],
  },
  {
    step: "03",
    color: "from-emerald-500 to-accent",
    icon: (
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </svg>
    ),
    title: "AI Report Processing",
    subtitle: "Most powerful step",
    items: [
      "OCR + medical entity extraction",
      "Abnormality & risk detection",
      "Patient-friendly plain-language summary",
    ],
  },
  {
    step: "04",
    color: "from-violet-500 to-purple-600",
    icon: (
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
        />
      </svg>
    ),
    title: "Doctor Recommendation",
    subtitle: "AI-matched specialist",
    items: [
      "Symptoms + labs + age analysis",
      "Specialization suggestion",
      "Urgency priority scoring",
    ],
  },
  {
    step: "05",
    color: "from-amber-500 to-gold",
    icon: (
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
        />
      </svg>
    ),
    title: "Doctor Review",
    subtitle: "Async expert response",
    items: [
      "View AI insights & extractions",
      "Add clinical opinion",
      "Upload prescription & guidance",
    ],
  },
  {
    step: "06",
    color: "from-rose-500 to-coral",
    icon: (
      <svg
        className="w-6 h-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    title: "Health Timeline",
    subtitle: "Longitudinal health journey",
    items: [
      "All reports + AI summaries",
      "Trend graphs & comparisons",
      "Doctor feedback history",
    ],
  },
];

const FEATURES = [
  {
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
    title: "PDF Report Analysis",
    desc: "Upload blood tests, MRIs, prescriptions. Our AI extracts values, detects abnormalities, and explains in plain language.",
  },
  {
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </svg>
    ),
    title: "Gemini AI Summaries",
    desc: "Powered by Google Gemini. Converts complex medical reports into clear, actionable insights for both patients and doctors.",
  },
  {
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    ),
    title: "Doctor Collaboration",
    desc: "Doctors review AI insights, add medical opinions, upload prescriptions. All async — no live calls required.",
  },
  {
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    title: "Health Timeline",
    desc: "Longitudinal health tracking. See your complete history: reports, AI summaries, trends, and doctor feedback over time.",
  },
];

export default function Home() {
  const { token } = useAuthStore();

  return (
    <div className="min-h-screen bg-dark text-white">
      {/* ── HERO ── */}
      <section className="relative overflow-hidden py-24 px-6">
        {/* Background orbs */}
        <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-secondary/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 -left-24 w-80 h-80 rounded-full bg-primary/30 blur-3xl pointer-events-none" />

        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left column */}
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/30 mb-6">
                <div className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
                <span className="text-secondary text-xs font-semibold tracking-widest uppercase">
                  MEDO SHIELD AI Platform
                </span>
              </div>

              <h1 className="text-5xl md:text-6xl font-bold leading-tight">
                Smart health care,{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary to-accent block mt-1">
                  from upload to insight.
                </span>
              </h1>

              <p className="text-slate-300 mt-6 text-lg leading-relaxed max-w-xl">
                Upload your medical reports, get AI-powered plain-language
                summaries, connect with doctors for expert review, and track
                your complete health journey — all in one platform.
              </p>

              <div className="flex flex-wrap gap-3 mt-8">
                {token ? (
                  <Link
                    to="/dashboard"
                    className="btn-teal text-base px-8 py-3.5"
                  >
                    Go to Dashboard
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/register"
                      className="btn-teal text-base px-8 py-3.5"
                    >
                      Get Started Free
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </Link>
                    <Link
                      to="/login"
                      className="px-6 py-3 rounded-lg bg-white/10 backdrop-blur border border-white/30 text-white hover:bg-secondary hover:text-white transition duration-300"
                    >
                      Patient Login
                    </Link>

                    <Link
                      to="/doctor-login"
                      className="px-6 py-3 rounded-lg bg-white/10 backdrop-blur border border-white/30 text-white hover:bg-secondary hover:text-white transition duration-300"
                    >
                      Doctor Login
                    </Link>
                  </>
                )}
              </div>

              {/* Quick stats */}
              <div className="mt-10 grid grid-cols-3 gap-4">
                {[
                  { label: "AI Reports", value: "Gemini-Powered" },
                  { label: "Data Security", value: "JWT Encrypted" },
                  { label: "Real-time", value: "Live Insights" },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="bg-white/5 border border-white/10 rounded-xl p-3"
                  >
                    <p className="text-xs text-slate-400 uppercase tracking-widest">
                      {s.label}
                    </p>
                    <p className="text-sm font-semibold mt-1 text-white">
                      {s.value}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right column — live status card */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-6">
                <p className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                  AI Report Pipeline
                </p>
                <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Active
                </span>
              </div>
              <div className="space-y-3">
                {[
                  {
                    label: "PDF Upload",
                    status: "Ready",
                    color: "text-emerald-400",
                  },
                  {
                    label: "OCR Extraction",
                    status: "AI Processing",
                    color: "text-secondary",
                  },
                  {
                    label: "Risk Detection",
                    status: "Gemini AI",
                    color: "text-secondary",
                  },
                  {
                    label: "Plain Summary",
                    status: "Generated",
                    color: "text-emerald-400",
                  },
                  {
                    label: "Doctor Review",
                    status: "Async Queue",
                    color: "text-amber-400",
                  },
                  {
                    label: "Health Timeline",
                    status: "Updated",
                    color: "text-emerald-400",
                  },
                ].map((row, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2.5 border-b border-white/5"
                  >
                    <span className="text-sm text-slate-300">{row.label}</span>
                    <span className={`text-xs font-semibold ${row.color}`}>
                      {row.status}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 bg-secondary/10 border border-secondary/30 rounded-xl">
                <p className="text-xs text-secondary font-semibold uppercase tracking-wider mb-1">
                  Latest AI Insight
                </p>
                <p className="text-sm text-slate-300 italic">
                  "Your hemoglobin is slightly low, which may indicate mild
                  anemia. Iron-rich diet and a general physician visit is
                  recommended."
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="bg-[#0f172a] py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-secondary text-xs uppercase tracking-widest font-semibold mb-3">
              Key Features
            </p>
            <h2 className="text-4xl font-bold">Everything in one portal</h2>
            <p className="text-slate-400 mt-4 max-w-2xl mx-auto">
              From report upload to expert doctor review — MEDO SHIELD AI
              handles every step of your health journey.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/8 hover:border-secondary/30 transition-all duration-300 group"
              >
                <div className="w-12 h-12 rounded-xl bg-secondary/20 flex items-center justify-center mb-4 text-secondary group-hover:bg-secondary/30 transition-colors">
                  {f.icon}
                </div>
                <h3 className="text-lg font-bold mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FLOW STEPS ── */}
      <section className="py-20 px-6 bg-dark">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-secondary text-xs uppercase tracking-widest font-semibold mb-3">
              System Workflow
            </p>
            <h2 className="text-4xl font-bold">Step-by-step care journey</h2>
            <p className="text-slate-400 mt-4 max-w-2xl mx-auto">
              A clean, structured workflow that keeps patients informed and
              doctors in full control.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FLOW_STEPS.map((s) => (
              <div
                key={s.step}
                className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-secondary/30 transition-all duration-300"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${s.color} flex items-center justify-center flex-shrink-0`}
                  >
                    {s.icon}
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-semibold">
                      Step {s.step}
                    </p>
                    <h3 className="text-base font-bold">{s.title}</h3>
                    <p className="text-xs text-secondary">{s.subtitle}</p>
                  </div>
                </div>
                <ul className="space-y-1.5">
                  {s.items.map((item) => (
                    <li
                      key={item}
                      className="flex items-start gap-2 text-sm text-slate-400"
                    >
                      <span className="text-secondary mt-0.5 flex-shrink-0">
                        ›
                      </span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PATIENT / DOCTOR COLUMNS ── */}
      <section className="py-20 px-6 bg-[#0f172a]">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-8">
          {/* Patient */}
          <div className="bg-white/5 border border-white/10 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-secondary/20 flex items-center justify-center text-secondary">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold">Patient Portal</h2>
            </div>
            <p className="text-slate-400 mb-6">
              Everything you need to manage your health digitally.
            </p>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                { t: "Medical PDFs", d: "Blood tests, MRI, prescriptions" },
                { t: "Symptom Tracking", d: "Text queries with context" },
                { t: "Videos & Images", d: "Gait, tremor, posture" },
                { t: "Health History", d: "Past reports and summaries" },
              ].map((item) => (
                <div
                  key={item.t}
                  className="bg-dark/60 border border-white/10 rounded-xl p-4"
                >
                  <p className="font-semibold text-sm mb-1">{item.t}</p>
                  <p className="text-xs text-slate-400">{item.d}</p>
                </div>
              ))}
            </div>
            <div className="mt-6 flex gap-3">
              <Link to="/register" className="btn-teal text-sm">
                Create Account
              </Link>
              <Link
                to="/login"
                className="px-6 py-3 rounded-lg bg-white/10 backdrop-blur border border-white/30 text-white hover:bg-secondary hover:text-white transition duration-300"
              >
                Patient Login
              </Link>
            </div> 
          </div>

          {/* Doctor */}
          <div className="bg-gradient-to-br from-secondary/10 to-primary/20 border border-secondary/20 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-secondary/30 flex items-center justify-center text-secondary">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold">Doctor Portal</h2>
            </div>
            <p className="text-slate-300 mb-6">
              Asynchronous review model — no live calls needed.
            </p>
            <ol className="space-y-3">
              {[
                "Review AI extracted test results and risk summaries",
                "Provide clinical opinion and medical adjustments",
                "Upload prescriptions or health guidance",
                "Patient timeline updated automatically",
              ].map((step, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-sm text-slate-300"
                >
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-secondary/30 text-secondary text-xs flex items-center justify-center font-bold mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
            <Link
              to="/doctor-login"
              className="mt-8 btn-teal text-sm w-full justify-center"
            >
              Enter Doctor Portal
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-6 bg-dark text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold">
            Ready for smarter health care?
          </h2>
          <p className="text-slate-400 mt-4 text-lg">
            All modules are connected, clean, and easy to use.
          </p>
          <div className="flex flex-wrap gap-4 justify-center mt-8">
            <Link to="/register" className="btn-teal text-base px-8 py-3.5">
              Create Patient Account
            </Link>
            <Link
              to="/doctor-login"
              className="px-6 py-3 rounded-lg bg-white/10 backdrop-blur border border-white/30 text-white hover:bg-secondary hover:text-white transition duration-300"
            >
              Doctor Portal
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="bg-primary/60 border-t border-white/10 py-8 px-6 text-center">
        <p className="text-slate-400 text-sm">
          &copy; 2026{" "}
          <span className="text-secondary font-semibold">MEDO SHIELD AI</span> ·
          Privacy-First · Gemini AI Powered · Secure
        </p>
      </footer>
    </div>
  );
}
