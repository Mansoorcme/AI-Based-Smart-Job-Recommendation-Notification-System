import { useState, useEffect, useRef, useCallback } from "react";

const API = "http://localhost:5000/api";
const post = (url, body) =>
  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(r => r.json());
const postForm = (url, form) =>
  fetch(url, { method: "POST", body: form }).then(r => r.json());

/* ─── GLOBAL STYLES ─────────────────────────────────────────────────────── */
const STYLES = `
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300;12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=DM+Mono:wght@300;400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --white:#ffffff;--off:#f7f8fc;--off2:#f0f2f9;
  --ink:#0d0f1c;--ink2:#2d2f45;--ink3:#6b6e8a;
  --violet:#5b4cf5;--violet-l:#7b6ff8;--violet-xl:#ede9fe;
  --green:#16a34a;--green-l:#dcfce7;
  --amber:#d97706;--amber-l:#fef3c7;
  --red:#dc2626;--red-l:#fee2e2;
  --blue:#0ea5e9;--blue-l:#e0f2fe;
  --border:#e4e6f0;--border2:#d1d4e8;
  --shadow-sm:0 1px 3px rgba(13,15,28,.06),0 1px 2px rgba(13,15,28,.04);
  --shadow:0 4px 16px rgba(13,15,28,.08),0 2px 4px rgba(13,15,28,.04);
  --shadow-lg:0 12px 40px rgba(13,15,28,.12),0 4px 8px rgba(13,15,28,.06);
  --shadow-violet:0 8px 32px rgba(91,76,245,.22);
  --radius:14px;--radius-sm:8px;--radius-lg:20px;
  --font:'Bricolage Grotesque',sans-serif;
  --mono:'DM Mono',monospace;
}
html,body,#root{height:100%;background:var(--white);color:var(--ink);font-family:var(--font);-webkit-font-smoothing:antialiased}

/* ── NAV ── */
.nav{
  position:sticky;top:0;z-index:100;
  background:rgba(255,255,255,.88);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 40px;height:64px;
}
.nav-logo{display:flex;align-items:center;gap:9px;font-weight:800;font-size:19px;color:var(--ink);text-decoration:none}
.nav-logo-icon{width:34px;height:34px;background:var(--violet);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px}
.nav-links{display:flex;align-items:center;gap:4px}
.nav-link{padding:7px 15px;border-radius:8px;font-size:14px;font-weight:600;color:var(--ink3);cursor:pointer;transition:all .15s;border:none;background:none}
.nav-link:hover{color:var(--ink);background:var(--off)}
.nav-link.active{color:var(--violet);background:var(--violet-xl)}
.nav-cta{padding:9px 20px;background:var(--violet);color:#fff;border:none;border-radius:9px;font-size:14px;font-weight:700;cursor:pointer;transition:all .18s;font-family:var(--font)}
.nav-cta:hover{background:var(--violet-l);box-shadow:var(--shadow-violet)}

/* ── HERO ── */
.hero{
  padding:80px 40px 60px;max-width:1280px;margin:0 auto;
  display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center;
}
.hero-eyebrow{display:inline-flex;align-items:center;gap:7px;background:var(--violet-xl);color:var(--violet);padding:5px 13px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.3px;margin-bottom:22px}
.hero-eyebrow-dot{width:6px;height:6px;background:var(--violet);border-radius:50%;animation:pulse-dot 2s ease-in-out infinite}
@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(.8)}}
.hero-title{font-size:52px;font-weight:800;line-height:1.1;letter-spacing:-1.5px;color:var(--ink);margin-bottom:22px}
.hero-title span{color:var(--violet)}
.hero-sub{font-size:17px;color:var(--ink3);line-height:1.65;margin-bottom:34px;font-weight:400}
.hero-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.hero-trust{margin-top:40px;display:flex;align-items:center;gap:10px}
.hero-avatars{display:flex}
.hero-avatar{width:30px;height:30px;border-radius:50%;border:2px solid var(--white);background:var(--violet-xl);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--violet);margin-left:-8px}
.hero-avatar:first-child{margin-left:0}
.hero-trust-text{font-size:13px;color:var(--ink3);font-weight:500}
.hero-trust-text strong{color:var(--ink)}

/* ── HERO CARD (right side) ── */
.hero-card{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow-lg);padding:28px;position:relative}
.hero-card::before{content:'';position:absolute;top:-1px;left:24px;right:24px;height:3px;background:linear-gradient(90deg,var(--violet),#a78bfa);border-radius:0 0 4px 4px}
.hero-card-label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:var(--ink3);margin-bottom:14px}
.upload-zone{
  border:2px dashed var(--border2);border-radius:var(--radius);padding:36px 24px;
  text-align:center;cursor:pointer;transition:all .2s;background:var(--off);
}
.upload-zone:hover,.upload-zone.drag{border-color:var(--violet);background:var(--violet-xl)}
.upload-zone-icon{font-size:32px;margin-bottom:10px}
.upload-zone-title{font-size:15px;font-weight:700;color:var(--ink);margin-bottom:4px}
.upload-zone-sub{font-size:12px;color:var(--ink3)}
.mini-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:16px}
.mini-stat{background:var(--off);border:1px solid var(--border);border-radius:10px;padding:12px;text-align:center}
.mini-stat-num{font-size:20px;font-weight:800;color:var(--violet)}
.mini-stat-lbl{font-size:10px;color:var(--ink3);font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}

/* ── MARQUEE ── */
.marquee-wrap{background:var(--off);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:20px 0;overflow:hidden;position:relative}
.marquee-label{text-align:center;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--ink3);margin-bottom:16px}
.marquee-track{display:flex;gap:0;width:max-content;animation:marquee 30s linear infinite}
@keyframes marquee{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.marquee-item{display:flex;align-items:center;gap:8px;padding:0 36px;font-size:14px;font-weight:700;color:var(--ink2);white-space:nowrap}
.marquee-item-dot{width:5px;height:5px;border-radius:50%;background:var(--violet-l)}

/* ── SECTION ── */
.section{padding:80px 40px;max-width:1200px;margin:0 auto}
.section-center{text-align:center;max-width:680px;margin:0 auto 56px}
.section-badge{display:inline-flex;align-items:center;gap:6px;background:var(--violet-xl);color:var(--violet);padding:5px 13px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.3px;margin-bottom:16px}
.section-title{font-size:38px;font-weight:800;letter-spacing:-1px;color:var(--ink);line-height:1.15;margin-bottom:14px}
.section-sub{font-size:16px;color:var(--ink3);line-height:1.6}

/* ── FEATURE GRID ── */
.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.feature-card{
  background:var(--white);border:1px solid var(--border);border-radius:var(--radius);
  padding:28px;cursor:pointer;transition:all .2s;position:relative;overflow:hidden;
}
.feature-card:hover{border-color:var(--violet-l);box-shadow:var(--shadow);transform:translateY(-2px)}
.feature-card.active{border-color:var(--violet);box-shadow:var(--shadow-violet);background:linear-gradient(135deg,rgba(91,76,245,.03),var(--white))}
.feature-icon{width:44px;height:44px;border-radius:11px;background:var(--violet-xl);display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:16px}
.feature-title{font-size:16px;font-weight:700;color:var(--ink);margin-bottom:7px}
.feature-desc{font-size:13px;color:var(--ink3);line-height:1.6}
.feature-tag{display:inline-block;font-size:10px;font-weight:700;padding:3px 9px;border-radius:20px;margin-top:12px;background:var(--violet-xl);color:var(--violet)}

/* ── APP PANEL (main workspace) ── */
.app-outer{background:var(--off);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:60px 0; flex: 1;}
.app-inner{max-width:1400px;margin:0 auto;padding:0 40px;display:grid;grid-template-columns:200px 1fr;gap:24px;align-items:start}
.app-sidebar{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;box-shadow:var(--shadow-sm);position:sticky;top:88px}
.app-sidebar-header{padding:12px 8px 16px;border-bottom:1px solid var(--border);margin-bottom:12px}
.app-sidebar-name{font-size:15px;font-weight:800;color:var(--ink)}
.app-sidebar-email{font-size:12px;color:var(--ink3);margin-top:2px;font-family:var(--mono)}
.app-nav-item{display:flex;align-items:center;gap:10px;padding:11px 12px;border-radius:10px;cursor:pointer;transition:all .15s;font-size:13px;font-weight:600;color:var(--ink3)}
.app-nav-item:hover{background:var(--off);color:var(--ink)}
.app-nav-item.active{background:var(--violet-xl);color:var(--violet)}
.app-nav-icon{width:32px;height:32px;border-radius:8px;background:var(--off);display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;transition:background .15s}
.app-nav-item.active .app-nav-icon{background:rgba(91,76,245,.12)}
.app-nav-divider{height:1px;background:var(--border);margin:10px 0}
.app-sidebar-stat{padding:10px 12px;background:var(--off);border-radius:10px;margin-top:12px}
.app-sidebar-stat-row{display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:5px}
.app-sidebar-stat-row:last-child{margin-bottom:0}
.app-sidebar-stat-label{color:var(--ink3);font-weight:500}
.app-sidebar-stat-val{font-weight:700;color:var(--violet);font-family:var(--mono)}

/* ── PANEL CONTENT ── */
.panel{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow-sm)}
.panel-header{padding:24px 28px 20px;border-bottom:1px solid var(--border)}
.panel-title{font-size:20px;font-weight:800;color:var(--ink);letter-spacing:-.4px}
.panel-sub{font-size:13px;color:var(--ink3);margin-top:4px}
.panel-body{padding:28px}
.panel-section{margin-bottom:28px}
.panel-section:last-child{margin-bottom:0}

/* ── FORM ELEMENTS ── */
.form-label{font-size:12px;font-weight:700;color:var(--ink2);letter-spacing:.2px;display:block;margin-bottom:7px}
.form-input{
  width:100%;padding:11px 14px;background:var(--off);border:1px solid var(--border);
  border-radius:var(--radius-sm);color:var(--ink);font-family:var(--font);font-size:14px;
  outline:none;transition:border-color .15s,box-shadow .15s;
}
.form-input:focus{border-color:var(--violet);box-shadow:0 0 0 3px rgba(91,76,245,.1);background:var(--white)}
.form-input::placeholder{color:var(--ink3)}
.form-textarea{resize:vertical;min-height:140px;line-height:1.6}
.form-select{
  width:100%;padding:11px 14px;background:var(--off);border:1px solid var(--border);
  border-radius:var(--radius-sm);color:var(--ink);font-family:var(--font);font-size:14px;
  outline:none;cursor:pointer;
}
.form-select:focus{border-color:var(--violet);box-shadow:0 0 0 3px rgba(91,76,245,.1)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-row3{display:grid;grid-template-columns:2fr 1fr 1fr;gap:16px}
.form-group{margin-bottom:18px}

/* ── BUTTONS ── */
.btn{display:inline-flex;align-items:center;gap:8px;padding:11px 22px;border-radius:9px;border:none;font-family:var(--font);font-size:14px;font-weight:700;cursor:pointer;transition:all .18s;letter-spacing:-.1px}
.btn-violet{background:var(--violet);color:#fff;box-shadow:0 2px 8px rgba(91,76,245,.25)}
.btn-violet:hover{background:var(--violet-l);box-shadow:var(--shadow-violet)}
.btn-violet:disabled{opacity:.45;cursor:not-allowed;box-shadow:none}
.btn-white{background:var(--white);color:var(--ink);border:1.5px solid var(--border);box-shadow:var(--shadow-sm)}
.btn-white:hover{border-color:var(--border2);box-shadow:var(--shadow)}
.btn-outline{background:transparent;border:1.5px solid var(--border2);color:var(--ink3)}
.btn-outline:hover{border-color:var(--violet);color:var(--violet);background:var(--violet-xl)}
.btn-lg{padding:14px 30px;font-size:15px;border-radius:11px}
.btn-sm{padding:7px 14px;font-size:12px;border-radius:7px}
.btn-full{width:100%;justify-content:center}
.btn-green{background:#16a34a;color:#fff}
.btn-green:hover{background:#15803d}

/* ── TAGS / BADGES ── */
.tag{display:inline-flex;align-items:center;gap:5px;padding:5px 11px;border-radius:20px;font-size:12px;font-weight:600}
.tag-violet{background:var(--violet-xl);color:var(--violet)}
.tag-green{background:var(--green-l);color:var(--green)}
.tag-amber{background:var(--amber-l);color:var(--amber)}
.tag-blue{background:var(--blue-l);color:var(--blue)}
.tag-red{background:var(--red-l);color:var(--red)}
.skill-chip{display:inline-flex;align-items:center;background:var(--off);border:1px solid var(--border);color:var(--ink2);padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600;margin:3px;cursor:default;transition:all .15s}
.skill-chip:hover{border-color:var(--violet-l);background:var(--violet-xl);color:var(--violet)}
.role-pill{display:inline-flex;align-items:center;background:var(--violet-xl);border:1px solid transparent;color:var(--violet);padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;margin:3px;cursor:pointer;transition:all .15s}
.role-pill:hover,.role-pill.sel{background:var(--violet);color:#fff;border-color:var(--violet)}

/* ── ALERTS ── */
.alert{display:flex;align-items:flex-start;gap:10px;padding:13px 16px;border-radius:10px;font-size:13px;margin-bottom:14px;line-height:1.5}
.alert-info{background:var(--blue-l);color:#0369a1;border:1px solid #bae6fd}
.alert-success{background:var(--green-l);color:var(--green);border:1px solid #bbf7d0}
.alert-warn{background:var(--amber-l);color:var(--amber);border:1px solid #fde68a}
.alert-error{background:var(--red-l);color:var(--red);border:1px solid #fecaca}

/* ── JOB CARD ── */
.job-card{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;margin-bottom:12px;transition:all .18s;position:relative}
.job-card:hover{border-color:var(--border2);box-shadow:var(--shadow)}
.job-card-accent{position:absolute;left:0;top:14px;bottom:14px;width:3px;border-radius:0 3px 3px 0;background:var(--violet)}
.job-card-accent.green{background:var(--green)}
.job-card-accent.blue{background:var(--blue)}
.job-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:10px;padding-left:12px}
.job-title{font-size:15px;font-weight:700;color:var(--ink);line-height:1.3}
.job-company{font-size:13px;color:var(--ink3);margin-top:3px}
.job-meta{display:flex;flex-wrap:wrap;gap:8px;padding-left:12px;margin-bottom:10px}
.job-meta-item{display:flex;align-items:center;gap:4px;font-size:12px;color:var(--ink3)}
.job-desc{font-size:13px;color:var(--ink3);line-height:1.6;padding-left:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:12px}
.job-actions{display:flex;align-items:center;justify-content:space-between;padding-left:12px}
.apply-btn{display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:700;color:var(--violet);text-decoration:none;transition:gap .15s}
.apply-btn:hover{gap:8px}
.apply-btn.green{color:var(--green)}

/* ── ATS TABLE ── */
.ats-table{width:100%;border-collapse:collapse}
.ats-table th{text-align:left;padding:10px 16px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--ink3);background:var(--off);border-bottom:1px solid var(--border)}
.ats-table th:first-child{border-radius:8px 0 0 0}
.ats-table th:last-child{border-radius:0 8px 0 0}
.ats-table td{padding:14px 16px;border-bottom:1px solid var(--border);vertical-align:top;font-size:13px}
.ats-table tr:last-child td{border-bottom:none}
.ats-score{font-weight:800;font-size:15px;color:var(--violet);font-family:var(--mono)}
.ats-bar{height:5px;background:var(--off2);border-radius:3px;margin-top:5px;overflow:hidden}
.ats-bar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--violet),#a78bfa);transition:width .6s ease}

/* ── METRICS ── */
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
.metric-card{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:20px;text-align:center;transition:all .18s}
.metric-card:hover{border-color:var(--violet-l);box-shadow:var(--shadow-sm)}
.metric-num{font-size:26px;font-weight:800;color:var(--violet);font-family:var(--mono)}
.metric-label{font-size:11px;color:var(--ink3);font-weight:600;text-transform:uppercase;letter-spacing:.8px;margin-top:4px}

/* ── TABS ── */
.tabs-bar{display:flex;gap:4px;background:var(--off);padding:5px;border-radius:11px;margin-bottom:20px;border:1px solid var(--border)}
.tab-btn{flex:1;padding:9px;border-radius:8px;font-size:12px;font-weight:700;text-align:center;cursor:pointer;color:var(--ink3);transition:all .15s;border:none;background:none;font-family:var(--font)}
.tab-btn:hover{color:var(--ink)}
.tab-btn.active{background:var(--white);color:var(--violet);box-shadow:var(--shadow-sm)}

/* ── EMPTY ── */
.empty-state{text-align:center;padding:52px 24px}
.empty-icon{font-size:40px;margin-bottom:12px;opacity:.35}
.empty-title{font-size:15px;font-weight:700;color:var(--ink);margin-bottom:6px}
.empty-sub{font-size:13px;color:var(--ink3)}

/* ── SPINNER / LOADING ── */
.spin{width:18px;height:18px;border:2.5px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;display:inline-block;flex-shrink:0}
.spin-dark{border-color:rgba(91,76,245,.2);border-top-color:var(--violet)}
@keyframes spin{to{transform:rotate(360deg)}}
.skeleton{background:linear-gradient(90deg,var(--off),var(--off2),var(--off));background-size:200%;animation:sk 1.5s infinite;border-radius:8px}
@keyframes sk{from{background-position:200% 0}to{background-position:-200% 0}}
.loading-row{height:90px;margin-bottom:12px}

/* ── SIGNAL PILL ── */
.signal-pill{display:inline-flex;align-items:center;gap:7px;background:var(--off);border:1px solid var(--border);color:var(--ink2);padding:7px 14px;border-radius:9px;font-size:12px;font-weight:500;margin-bottom:16px}

/* ── PORTAL CHIP ── */
.portal-chip{display:inline-flex;align-items:center;gap:6px;background:var(--white);border:1px solid var(--border);padding:8px 14px;border-radius:10px;font-size:13px;font-weight:600;color:var(--ink2);text-decoration:none;margin:4px;transition:all .15s;box-shadow:var(--shadow-sm)}
.portal-chip:hover{border-color:var(--violet-l);color:var(--violet);box-shadow:var(--shadow)}

/* ── LANDING FEATURES ── */
.how-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:28px}
.how-card{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);padding:32px;box-shadow:var(--shadow-sm)}
.how-step{width:28px;height:28px;border-radius:50%;background:var(--violet);color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;margin-bottom:14px}
.how-title{font-size:17px;font-weight:800;color:var(--ink);margin-bottom:8px}
.how-desc{font-size:14px;color:var(--ink3);line-height:1.65}

/* ── FOOTER ── */
.footer{background:var(--ink);color:rgba(255,255,255,.55);text-align:center;padding:32px 40px;font-size:13px}
.footer strong{color:#fff}

/* ── MISC ── */
.divider{height:1px;background:var(--border);margin:24px 0}
.flex{display:flex;align-items:center;gap:12px}
.flex-between{display:flex;align-items:center;justify-content:space-between}
.mono{font-family:var(--mono)}
.fw8{font-weight:800}
.fs12{font-size:12px}
.fs13{font-size:13px}
.c-ink3{color:var(--ink3)}
.c-violet{color:var(--violet)}
.mb4{margin-bottom:4px}
.mb8{margin-bottom:8px}
.mb16{margin-bottom:16px}
.mb24{margin-bottom:24px}
.mt16{margin-top:16px}
.mt24{margin-top:24px}
.gap8{gap:8px}

@media(max-width:900px){
  .hero{grid-template-columns:1fr;gap:36px}
  .feature-grid{grid-template-columns:1fr 1fr}
  .app-inner{grid-template-columns:1fr}
  .app-sidebar{display:none}
  .metrics{grid-template-columns:1fr 1fr}
  .form-row3,.form-row{grid-template-columns:1fr}
  .nav-links{display:none}
  .section{padding:52px 20px}
  .hero{padding:48px 20px 36px}
}
`;

/* ─── SMALL HELPERS ──────────────────────────────────────────────────────── */
const Spin = ({ dark }) => <span className={`spin${dark ? " spin-dark" : ""}`} />;
const Alert = ({ type = "info", children }) => {
  const icons = { info: "ℹ️", success: "✓", warn: "⚠️", error: "✕" };
  return <div className={`alert alert-${type}`}><span>{icons[type]}</span><span>{children}</span></div>;
};
const SkeletonList = () => (
  <>{[...Array(3)].map((_, i) => <div key={i} className="skeleton loading-row" style={{ animationDelay: `${i * .15}s` }} />)}</>
);

/* ─── JOB CARD ───────────────────────────────────────────────────────────── */
const JobCard = ({ job }) => {
  const src = (job.source || "").toLowerCase();
  const accentClass = src.includes("adzuna") ? "" : src.includes("aicte") ? "blue" : "green";
  const applyClass  = src.includes("adzuna") ? "" : "green";
  const tagColor    = src.includes("adzuna") ? "tag-violet" : src.includes("aicte") ? "tag-blue" : "tag-green";
  const sal = job.salary ? `₹${Number(job.salary).toLocaleString("en-IN")}` : null;
  return (
    <div className="job-card">
      <div className={`job-card-accent ${accentClass}`} />
      <div className="job-card-head">
        <div>
          <div className="job-title">{job.title}</div>
          <div className="job-company">{job.company}</div>
        </div>
        <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:5, flexShrink:0 }}>
          <span className={`tag ${tagColor}`}>{job.source}</span>
          {sal && <span className="mono" style={{ fontSize:13, fontWeight:700, color:"var(--green)" }}>{sal}</span>}
        </div>
      </div>
      <div className="job-meta">
        <span className="job-meta-item">📍 {job.location}</span>
        {job.description && <span className="job-meta-item">🏢 {job.company}</span>}
      </div>
      {job.description && <div className="job-desc">{job.description}</div>}
      <div className="job-actions">
        <a href={job.url} target="_blank" rel="noreferrer" className={`apply-btn ${applyClass}`}>
          Apply Now ↗
        </a>
        <span className="fs12 c-ink3">View details →</span>
      </div>
    </div>
  );
};

/* ─── ATS TABLE ──────────────────────────────────────────────────────────── */
const ATSTable = ({ rows }) => (
  <div style={{ borderRadius:10, border:"1px solid var(--border)", overflow:"hidden" }}>
    <table className="ats-table">
      <thead>
        <tr><th>Role</th><th>ATS Match</th><th>Matching Skills</th><th>Missing Skills</th></tr>
      </thead>
      <tbody>
        {rows.map((r, i) => {
          const pct = parseInt(r["ATS Score"]) || 0;
          return (
            <tr key={i}>
              <td><strong>{r.Role}</strong></td>
              <td>
                <div className="ats-score">{r["ATS Score"]}</div>
                <div className="ats-bar"><div className="ats-bar-fill" style={{ width: `${pct}%` }} /></div>
              </td>
              <td style={{ color:"var(--green)", fontSize:12, fontFamily:"var(--mono)" }}>{r["Matching Skills"]}</td>
              <td style={{ color:"var(--ink3)", fontSize:12, fontFamily:"var(--mono)" }}>{r["Missing Skills"]}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
);

/* ─── LANDING PAGE ───────────────────────────────────────────────────────── */
const LandingPage = ({ onGetStarted }) => {
  const fileRef = useRef();
  const [drag, setDrag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const handleFile = useCallback(async (file) => {
    if (!file || file.type !== "application/pdf") { setErr("Please upload a PDF resume."); return; }
    setLoading(true); setErr(null);
    try {
      const fd = new FormData();
      fd.append("resume", file);
      const data = await postForm(`${API}/resume/parse`, fd);
      if (!data.ok) throw new Error(data.error);
      onGetStarted(data);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }, [onGetStarted]);

  const companies = ["Google","Microsoft","Amazon","Meta","Netflix","Flipkart","Adobe","Atlassian","Uber","Airbnb","Spotify","Tesla","Stripe","Shopify","Oracle","IBM"];

  const features = [
    { icon:"📄", title:"AI Resume Parser",    desc:"Upload your PDF — spaCy NLP extracts skills, experience, and domains instantly. Zero manual input.",             tag:"Instant" },
    { icon:"🔍", title:"Smart Job Search",    desc:"Searches Adzuna API, company career pages, AICTE internship portal, and startup.jobs simultaneously.",          tag:"4 Sources" },
    { icon:"🧠", title:"ATS Role Matching",   desc:"Gemini AI analyses your skills and calculates ATS match scores for the most suitable job roles.",                tag:"Gemini AI" },
    { icon:"📧", title:"Email Job Alerts",    desc:"Get instant or daily scheduled job alerts sent straight to your inbox with apply links included.",              tag:"Auto" },
    { icon:"📑", title:"ATS Resume Builder",  desc:"Paste any job description — Gemini rewrites your resume to match it and exports an ATS-optimised PDF.",         tag:"1-Click PDF" },
    { icon:"🏢", title:"Career Portal Links", desc:"Matched career pages from 100+ company portals relevant to your domain — verified working links only.",         tag:"100+ Companies" },
  ];

  return (
    <div>
      {/* ── Hero ── */}
      <div className="hero">
        <div>
          <div className="hero-eyebrow">
            <span className="hero-eyebrow-dot" />
            AI-Powered Job Search Platform
          </div>
          <h1 className="hero-title">
            Land your <span>dream job</span> faster with AI
          </h1>
          <p className="hero-sub">
            Upload your resume once. Get matched to live jobs from Adzuna, company career pages, and AICTE internships — powered by Gemini AI with ATS scoring, auto-alerts, and PDF resume generation.
          </p>
          <div className="hero-actions">
            <button className="btn btn-violet btn-lg" onClick={() => fileRef.current?.click()}>
              {loading ? <><Spin /> Parsing…</> : "⚡ Get Started Free"}
            </button>
            <button className="btn btn-white btn-lg" onClick={() => document.getElementById("features")?.scrollIntoView({ behavior:"smooth" })}>
              See How It Works
            </button>
          </div>
          {err && <div className="mt16"><Alert type="error">{err}</Alert></div>}
          <input ref={fileRef} type="file" accept=".pdf" style={{ display:"none" }} onChange={e => handleFile(e.target.files[0])} />
          <div className="hero-trust">
            <div className="hero-avatars">
              {["RK","AS","PM","SJ","NM"].map(n => <div key={n} className="hero-avatar">{n}</div>)}
            </div>
            <div className="hero-trust-text"><strong>12,000+</strong> job seekers using the platform</div>
          </div>
        </div>

        {/* ── Hero right card ── */}
        <div className="hero-card">
          <div className="hero-card-label">📄 Resume Upload</div>
          <label
            className={`upload-zone ${drag ? "drag" : ""}`}
            onDragOver={e => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={e => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0]); }}
            onClick={() => fileRef.current?.click()}
            style={{ cursor:"pointer" }}
          >
            {loading
              ? <><div className="upload-zone-icon"><Spin dark /></div><div className="upload-zone-title">Parsing your resume…</div><div className="upload-zone-sub">NLP extraction in progress</div></>
              : <><div className="upload-zone-icon">📄</div><div className="upload-zone-title">Drop your PDF resume here</div><div className="upload-zone-sub">or click to browse · PDF only</div></>
            }
          </label>
          <div className="mini-stats">
            {[["4","Job Sources"],["100+","Companies"],["Gemini","AI Engine"]].map(([n,l]) => (
              <div className="mini-stat" key={l}>
                <div className="mini-stat-num">{n}</div>
                <div className="mini-stat-lbl">{l}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:16, display:"flex", flexWrap:"wrap", gap:5 }}>
            {["Python Developer","Data Scientist","ML Engineer","Frontend Dev","DevOps"].map(r => (
              <span key={r} className="role-pill" style={{ fontSize:11, padding:"4px 10px" }}>{r}</span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Features ── */}
      <div className="section" id="features">
        <div className="section-center">
          <div className="section-badge">✦ Features</div>
          <h2 className="section-title">Everything you need for your job search</h2>
          <p className="section-sub">One platform — AI parsing, live job search, ATS scoring, email alerts, and resume building.</p>
        </div>
        <div className="feature-grid">
          {features.map(f => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
              <div className="feature-tag">{f.tag}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── How it works ── */}
      <div style={{ background:"var(--off)", borderTop:"1px solid var(--border)", borderBottom:"1px solid var(--border)", padding:"80px 0" }}>
        <div className="section" style={{ paddingTop:0, paddingBottom:0 }}>
          <div className="section-center">
            <div className="section-badge">✦ How It Works</div>
            <h2 className="section-title">From resume to job in 4 steps</h2>
          </div>
          <div className="how-grid">
            {[
              ["Upload Resume","Drop your PDF — spaCy NLP instantly extracts name, email, skills, years of experience, and inferred job domains."],
              ["Get Role Matches","Gemini AI analyses your skills and produces ATS match scores for the top 3-5 roles that fit your profile."],
              ["Search Live Jobs","We search Adzuna, career pages from 100+ companies, AICTE internship portal, and startup.jobs — all at once."],
              ["Apply & Alert","Click Apply Now on any result. Set up daily email alerts to get fresh jobs in your inbox automatically."],
            ].map(([title, desc], i) => (
              <div className="how-card" key={title}>
                <div className="how-step">{i + 1}</div>
                <div className="how-title">{title}</div>
                <div className="how-desc">{desc}</div>
              </div>
            ))}
          </div>
          <div style={{ textAlign:"center", marginTop:40 }}>
            <button className="btn btn-violet btn-lg" onClick={() => fileRef.current?.click()}>
              Start Now — It's Free ↗
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ─── APP PAGES ──────────────────────────────────────────────────────────── */

/* ── Profile ── */
const ProfilePage = ({ info, suggestedRoles, atsRows, atsLoading }) => (
  <div className="panel">
    <div className="panel-header">
      <div className="panel-title">Your Profile</div>
      <div className="panel-sub">Parsed from your resume via NLP · {info.experience_signals}</div>
    </div>
    <div className="panel-body">
      <div className="metrics">
        {[[info.skills?.length ?? 0,"Skills Detected"],[info.experience_years ?? "—","Experience (yrs)"],[info.projects_count ?? 0,"Projects Found"],[info.experience_level,"Level"]].map(([n,l]) => (
          <div className="metric-card" key={l}><div className="metric-num">{n}</div><div className="metric-label">{l}</div></div>
        ))}
      </div>

      {info.skills?.length > 0 && (
        <div className="panel-section">
          <div className="form-label" style={{ marginBottom:10 }}>Extracted Skills ({info.skills.length})</div>
          <div>{info.skills.map(s => <span key={s} className="skill-chip">{s}</span>)}</div>
        </div>
      )}

      {suggestedRoles?.length > 0 && (
        <div className="panel-section">
          <div className="form-label" style={{ marginBottom:10 }}>AI Suggested Roles</div>
          <div>{suggestedRoles.map(r => <span key={r} className="role-pill">{r}</span>)}</div>
        </div>
      )}

      <div className="divider" />

      <div className="panel-section">
        <div className="form-label" style={{ marginBottom:14 }}>ATS Role Match Analysis</div>
        {atsLoading
          ? <SkeletonList />
          : atsRows?.length
            ? <ATSTable rows={atsRows} />
            : <div className="empty-state"><div className="empty-icon">📊</div><div className="empty-title">Analysis unavailable</div><div className="empty-sub">Gemini API may be unreachable</div></div>
        }
      </div>

      {info.education && (
        <>
          <div className="divider" />
          <div className="panel-section">
            <div className="form-label" style={{ marginBottom:8 }}>Education</div>
            <div className="fw8 fs13">{info.education}</div>
          </div>
        </>
      )}
    </div>
  </div>
);

/* ── Jobs ── */
const JobsPage = ({ info, suggestedRoles, onResults, initialResults }) => {
  const [query,    setQuery]    = useState("");
  const [pickRole, setPickRole] = useState("");
  const [expLevel, setExpLevel] = useState(info?.experience_level || "Fresher");
  const [location, setLocation] = useState(info?.location || "");
  const [country,  setCountry]  = useState("India");
  const [tab,      setTab]      = useState(0);
  const [loading,  setLoading]  = useState(false);
  const [results,  setResults]  = useState(initialResults || null);
  const [error,    setError]    = useState(null);

  const search = async () => {
    setLoading(true); setError(null);
    try {
      const data = await post(`${API}/jobs/search`, {
        query:     (query || pickRole).trim(),
        skills:    info?.skills || [],
        domains:   info?.domains || [],
        exp_level: expLevel,
        location,
        country,
      });
      if (!data.ok) throw new Error(data.error || "Search failed");
      setResults(data);
      onResults?.(data);
      setTab(0);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex-between">
          <div>
            <div className="panel-title">Job Search</div>
            <div className="panel-sub">Adzuna · Career Pages · AICTE · Startup.jobs</div>
          </div>
          {results && (
            <span className="tag tag-green">
              {(results.adzuna_jobs?.length || 0) + (results.career_jobs?.length || 0) + (results.aicte_jobs?.length || 0)} results
            </span>
          )}
        </div>
      </div>
      <div className="panel-body">
        {/* Suggested roles */}
        {suggestedRoles?.length > 0 && (
          <div className="mb16">
            <div className="form-label mb8">Suggested roles from your resume</div>
            <div>{suggestedRoles.map(r => (
              <span key={r} className={`role-pill ${pickRole === r ? "sel" : ""}`} onClick={() => { setPickRole(r); setQuery(""); }}>{r}</span>
            ))}</div>
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Role or Keyword</label>
          <input className="form-input" placeholder="e.g. Machine Learning Engineer, Backend, NLP…"
            value={query} onChange={e => { setQuery(e.target.value); setPickRole(""); }} />
        </div>

        <div className="form-row3">
          <div className="form-group">
            <label className="form-label">Experience Level</label>
            <select className="form-select" value={expLevel} onChange={e => setExpLevel(e.target.value)}>
              {["Fresher","0-2 yrs","2-4 yrs","5-10 yrs"].map(l => <option key={l}>{l}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Location</label>
            <input className="form-input" placeholder="Bangalore, Hyderabad…" value={location} onChange={e => setLocation(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Country</label>
            <select className="form-select" value={country} onChange={e => setCountry(e.target.value)}>
              {["India","USA","UK","Canada","Australia"].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <button className="btn btn-violet" onClick={search} disabled={loading} style={{ marginBottom: error || results ? 16 : 0 }}>
          {loading ? <><Spin /> Searching all sources…</> : "🚀 Search Jobs"}
        </button>

        {error && <Alert type="error">{error}</Alert>}

        {results && (
          <>
            <Alert type="success">
              <strong>{results.adzuna_jobs?.length}</strong> live jobs · <strong>{results.career_jobs?.length}</strong> career page listings · <strong>{results.aicte_jobs?.length}</strong> internships found
            </Alert>
            {results.adzuna_error && <Alert type="warn">{results.adzuna_error}</Alert>}

            <div className="tabs-bar">
              {[`Live Jobs (${results.adzuna_jobs?.length||0})`,`Career Pages (${results.career_jobs?.length||0})`,`Internships (${results.aicte_jobs?.length||0})`].map((t,i) => (
                <button key={t} className={`tab-btn ${tab===i?"active":""}`} onClick={() => setTab(i)}>{t}</button>
              ))}
            </div>

            {tab === 0 && (
              results.adzuna_jobs?.length
                ? results.adzuna_jobs.map((j,i) => <JobCard key={i} job={j} />)
                : <div className="empty-state"><div className="empty-icon">📭</div><div className="empty-title">No Adzuna results</div><div className="empty-sub">Try different keywords or remove the location filter</div></div>
            )}
            {tab === 1 && (
              results.career_jobs?.length
                ? results.career_jobs.map((j,i) => <JobCard key={i} job={j} />)
                : <div>
                    <Alert type="info">Career pages use JavaScript — visit them directly below:</Alert>
                    <div style={{ marginTop:12 }}>
                      {results.portal_matches?.map(p => (
                        <a key={p.title} className="portal-chip" href={p.link} target="_blank" rel="noreferrer">🏢 {p.title} ↗</a>
                      ))}
                    </div>
                  </div>
            )}
            {tab === 2 && (
              results.aicte_jobs?.length
                ? results.aicte_jobs.map((j,i) => <JobCard key={i} job={j} />)
                : <div className="empty-state"><div className="empty-icon">🎓</div><div className="empty-title">No internships matched</div><div className="empty-sub">Try broader search terms</div></div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

/* ── Email ── */
const EmailPage = ({ info, jobResults }) => {
  const [sender,    setSender]    = useState("");
  const [password,  setPassword]  = useState("");
  const [recipient, setRecipient] = useState("");
  const [expLevel,  setExpLevel]  = useState(info?.experience_level || "Fresher");
  const [previewHtml,setPreview]  = useState(null);
  const [sending,   setSending]   = useState(false);
  const [previewing,setPreviewing]= useState(false);
  const [status,    setStatus]    = useState(null);

  const allJobs = [...(jobResults?.adzuna_jobs||[]),...(jobResults?.career_jobs||[])].slice(0,12);
  const portals = jobResults?.portal_matches || [];
  const payload = { jobs:allJobs, portals, skills:info?.skills||[], exp_level:expLevel };

  const preview = async () => {
    setPreviewing(true);
    try {
      const data = await post(`${API}/email/preview`, payload);
      if (data.ok) setPreview(data.html);
    } finally { setPreviewing(false); }
  };

  const send = async () => {
    if (!sender||!password||!recipient) { setStatus({ type:"warn", msg:"Please fill in all email fields." }); return; }
    setSending(true); setStatus(null);
    try {
      const data = await post(`${API}/email/send`, { ...payload, sender, password, recipient });
      setStatus(data.ok ? { type:"success", msg:`✓ Email sent to ${recipient}` } : { type:"error", msg:data.error });
    } catch (e) { setStatus({ type:"error", msg:e.message }); }
    finally { setSending(false); }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">Email Job Alerts</div>
        <div className="panel-sub">Send instant alerts or schedule daily digests</div>
      </div>
      <div className="panel-body">
        {!jobResults && <Alert type="warn">Run a Job Search first — the email will include those live results.</Alert>}

        <div className="panel-section">
          <div className="form-label" style={{ fontSize:13, fontWeight:800, marginBottom:14 }}>Email Configuration</div>
          <Alert type="info">Use a Gmail App Password: Google Account → Security → App Passwords</Alert>
          <div className="form-row" style={{ marginTop:14 }}>
            <div className="form-group">
              <label className="form-label">Your Gmail Address</label>
              <input className="form-input" type="email" placeholder="you@gmail.com" value={sender} onChange={e => setSender(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">App Password</label>
              <input className="form-input" type="password" placeholder="16-character app password" value={password} onChange={e => setPassword(e.target.value)} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Send Alerts To</label>
              <input className="form-input" type="email" placeholder="recipient@example.com" value={recipient} onChange={e => setRecipient(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Experience Level</label>
              <select className="form-select" value={expLevel} onChange={e => setExpLevel(e.target.value)}>
                {["Fresher","0-2 yrs","2-4 yrs","5-10 yrs"].map(l => <option key={l}>{l}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="divider" />

        <div className="form-row" style={{ marginBottom:16 }}>
          <div>
            <div className="form-label" style={{ marginBottom:6 }}>⚡ Instant Alert</div>
            <div className="fs12 c-ink3" style={{ marginBottom:12 }}>Send right now with current search results</div>
            <button className="btn btn-violet" onClick={send} disabled={sending}>
              {sending ? <><Spin /> Sending…</> : "📬 Send Now"}
            </button>
          </div>
          <div>
            <div className="form-label" style={{ marginBottom:6 }}>👁 Preview Email</div>
            <div className="fs12 c-ink3" style={{ marginBottom:12 }}>See how the alert will look</div>
            <button className="btn btn-outline" onClick={preview} disabled={previewing}>
              {previewing ? <><Spin dark /> Loading…</> : "Preview Email"}
            </button>
          </div>
        </div>

        {status && <Alert type={status.type}>{status.msg}</Alert>}

        {previewHtml && (
          <div>
            <div className="form-label" style={{ marginBottom:10 }}>Email Preview</div>
            <div style={{ border:"1px solid var(--border)", borderRadius:12, overflow:"hidden" }}>
              <iframe srcDoc={previewHtml} height={580} title="Email Preview" style={{ width:"100%", border:"none", display:"block" }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/* ── ATS Resume ── */
const ATSPage = ({ info }) => {
  const [name,    setName]    = useState(info?.name || "");
  const [jd,      setJd]      = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);
  const [done,    setDone]    = useState(false);

  const generate = async () => {
    if (!jd.trim()) { setError("Please paste a job description first."); return; }
    if (!name.trim()) { setError("Please enter your name."); return; }
    setLoading(true); setError(null); setDone(false);
    try {
      const res = await fetch(`${API}/resume/build-pdf`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body:JSON.stringify({ resume_text:info?.resumeText||"", job_description:jd, candidate_name:name }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.error||"Generation failed"); }
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href = url; a.download = `ATS_Resume_${name.replace(/\s+/g,"_")}.pdf`; a.click();
      URL.revokeObjectURL(url);
      setDone(true);
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">ATS Resume Builder</div>
        <div className="panel-sub">Gemini AI rewrites your resume to match any job description</div>
      </div>
      <div className="panel-body">
        <Alert type="info">Paste the target job description below — Gemini rewrites your resume keywords, bullets, and summary to maximise ATS match, then exports a polished PDF.</Alert>
        <div style={{ marginTop:20 }}>
          <div className="form-group">
            <label className="form-label">Your Full Name</label>
            <input className="form-input" placeholder="e.g. Ravi Kumar" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Target Job Description</label>
            <textarea className="form-input form-textarea" placeholder="Paste the full job description here — the more detail, the better the resume match…" value={jd} onChange={e => setJd(e.target.value)} />
          </div>
          <button className="btn btn-violet" onClick={generate} disabled={loading}>
            {loading ? <><Spin /> Generating PDF…</> : "⚡ Generate ATS Resume PDF"}
          </button>
        </div>
        {error && <div className="mt16"><Alert type="error">{error}</Alert></div>}
        {done  && <div className="mt16"><Alert type="success">✓ PDF downloaded! Check your Downloads folder.</Alert></div>}

        <div className="divider" />
        <div className="form-label" style={{ marginBottom:14 }}>What Gemini optimises</div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
          {[["Professional Summary","Rewritten to mirror the JD's tone and keywords"],["Skills Section","Reordered to highlight most relevant skills for the role"],["Experience Bullets","Each bullet rewritten with impact metrics and JD keywords"],["ATS Keywords","Critical keywords embedded naturally throughout the resume"]].map(([t,d]) => (
            <div key={t} style={{ background:"var(--off)", border:"1px solid var(--border)", borderRadius:10, padding:16 }}>
              <div style={{ fontWeight:700, fontSize:13, marginBottom:5 }}>✦ {t}</div>
              <div style={{ fontSize:12, color:"var(--ink3)", lineHeight:1.6 }}>{d}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/* ─── ROOT APP ───────────────────────────────────────────────────────────── */
export default function App() {
  const [parseData,  setParseData]  = useState(null);
  const [atsRows,    setAtsRows]    = useState(null);
  const [atsLoading, setAtsLoading] = useState(false);
  const [jobResults, setJobResults] = useState(null);
  const [page,       setPage]       = useState("home");

  useEffect(() => {
    const el = document.createElement("style");
    el.textContent = STYLES;
    document.head.appendChild(el);
    return () => document.head.removeChild(el);
  }, []);

  const onGetStarted = useCallback(async (data) => {
    setParseData(data);
    setPage("profile");
    setAtsRows(null);
    const skills = data.info?.skills || [];
    if (skills.length === 0) return;
    setAtsLoading(true);
    try {
      const r = await post(`${API}/resume/ats-roles`, { skills });
      if (r.ok) setAtsRows(r.table_rows);
    } catch (_) {}
    finally { setAtsLoading(false); }
  }, []);

  const info           = parseData?.info ? { ...parseData.info, resumeText: parseData.resume_text } : null;
  const suggestedRoles = parseData?.suggested_roles || [];

  const APP_NAV = [
    { id:"profile", icon:"👤", label:"Profile" },
    { id:"jobs",    icon:"🔍", label:"Job Search" },
    { id:"email",   icon:"📧", label:"Email Alerts" },
    { id:"ats",     icon:"📑", label:"ATS Resume" },
  ];

  const isApp = page !== "home" && !!info;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* ── NAV ── */}
      <nav className="nav">
        <div className="nav-logo" onClick={() => setPage("home")} style={{ cursor:"pointer" }}>
          <div className="nav-logo-icon">🚀</div>
          JobRadar AI
        </div>
        <div className="nav-links">
          {!isApp && (
            <>
              <button className="nav-link" onClick={() => document.getElementById("features")?.scrollIntoView({ behavior:"smooth" })}>Features</button>
              <button className="nav-link" onClick={() => document.getElementById("features")?.scrollIntoView({ behavior:"smooth" })}>How it Works</button>
            </>
          )}
          {isApp && APP_NAV.map(n => (
            <button key={n.id} className={`nav-link ${page===n.id?"active":""}`} onClick={() => setPage(n.id)}>
              {n.icon} {n.label}
            </button>
          ))}
        </div>
        {!info
          ? <button className="nav-cta" onClick={() => setPage("home")}>Get Started Free →</button>
          : <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <span className="tag tag-green" style={{ fontSize:12 }}>✓ Resume Loaded</span>
              <button className="nav-cta" onClick={() => { setParseData(null); setPage("home"); }}>New Resume</button>
            </div>
        }
      </nav>

      {/* ── MAIN CONTENT ── */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {page === "home" && <LandingPage onGetStarted={onGetStarted} />}

        {/* ── APP WORKSPACE ── */}
        {isApp && (
          <div className="app-outer">
            <div className="app-inner">
              {/* Sidebar */}
              <aside className="app-sidebar">
                <div className="app-sidebar-header">
                  <div className="app-sidebar-name">{info.name || "Your Profile"}</div>
                  <div className="app-sidebar-email">{info.email}</div>
                </div>
                {APP_NAV.map(n => (
                  <div key={n.id} className={`app-nav-item ${page===n.id?"active":""}`} onClick={() => setPage(n.id)}>
                    <div className="app-nav-icon">{n.icon}</div>
                    {n.label}
                  </div>
                ))}
                <div className="app-nav-divider" />
                <div className="app-sidebar-stat">
                  <div className="app-sidebar-stat-row">
                    <span className="app-sidebar-stat-label">Skills</span>
                    <span className="app-sidebar-stat-val">{info.skills?.length}</span>
                  </div>
                  <div className="app-sidebar-stat-row">
                    <span className="app-sidebar-stat-label">Experience</span>
                    <span className="app-sidebar-stat-val">{info.experience_years}yr</span>
                  </div>
                  <div className="app-sidebar-stat-row">
                    <span className="app-sidebar-stat-label">Level</span>
                    <span className="app-sidebar-stat-val">{info.experience_level}</span>
                  </div>
                  {info.location && (
                    <div className="app-sidebar-stat-row">
                      <span className="app-sidebar-stat-label">Location</span>
                      <span className="app-sidebar-stat-val">{info.location}</span>
                    </div>
                  )}
                </div>
              </aside>

              {/* Main panel */}
              <main>
                {page === "profile" && <ProfilePage info={info} suggestedRoles={suggestedRoles} atsRows={atsRows} atsLoading={atsLoading} />}
                {page === "jobs"    && <JobsPage    info={info} suggestedRoles={suggestedRoles} onResults={setJobResults} initialResults={jobResults} />}
                {page === "email"   && <EmailPage   info={info} jobResults={jobResults} />}
                {page === "ats"     && <ATSPage     info={info} />}
              </main>
            </div>
          </div>
        )}
      </main>

      {/* ── FOOTER ── */}
      {page === "home" && (
        <footer className="footer">
          <strong>JobRadar AI</strong> · AI-Powered Job Search Platform · Built with Gemini AI + Adzuna API + spaCy NLP
        </footer>
      )}
    </div>
  );
}
