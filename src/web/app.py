"""AI SUMMIT 2026 — Conference Planning Intelligence.

Professional dashboard for CES/Web Summit-level conference planning.
5-tab structure: Dashboard / Research / Agenda / Speakers / Plan
"""

import io
import json
import os
from datetime import date, datetime

import httpx
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# === Config ===

def _get_api_base() -> str:
    if os.environ.get("API_BASE_URL"):
        return os.environ["API_BASE_URL"]
    try:
        return st.secrets["API_BASE_URL"]
    except (KeyError, FileNotFoundError):
        return "http://localhost:8000/api"

API_BASE = _get_api_base()

st.set_page_config(
    page_title="AI SUMMIT 2026",
    page_icon="./",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st_autorefresh(interval=60_000, limit=None, key="auto_refresh")


# ============================================================
# CSS — Professional White Theme (Linear/Notion-inspired)
# ============================================================

TRACK_COLORS = ["#2563eb", "#7c3aed", "#059669", "#d97706"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset ── */
.stApp {
    background: #f8f9fa;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1a1a1a;
}
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #eee; }
.stMarkdown { color: #374151; }
#MainMenu, header, footer { visibility: hidden; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #fff;
    border-bottom: 1px solid #e5e7eb;
    padding: 0 2rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.82rem;
    color: #9ca3af;
    padding: 0.85rem 1.5rem;
    border-bottom: 2px solid transparent;
    background: transparent;
    letter-spacing: -0.01em;
}
.stTabs [aria-selected="true"] {
    color: #111827 !important;
    border-bottom: 2px solid #111827 !important;
    background: transparent !important;
}

/* ── Page Header ── */
.page-header {
    background: #fff;
    padding: 1.6rem 2.5rem 1rem 2.5rem;
    margin: -1rem -1rem 0 -1rem;
    border-bottom: 1px solid #e5e7eb;
}
.page-header h1 {
    font-size: 1.3rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    letter-spacing: -0.5px;
}
.page-header .sub {
    color: #9ca3af;
    font-size: 0.78rem;
    margin-top: 0.1rem;
    font-weight: 400;
}

/* ── KPI Cards ── */
.kpi-item {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.kpi-num {
    font-size: 1.6rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
}
.kpi-lbl {
    font-size: 0.6rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 3px;
    font-weight: 500;
}

/* ── Section ── */
.sec-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 1.8rem 0 0.8rem 0;
}
.sec-count {
    display: inline-block;
    background: #f3f4f6;
    color: #6b7280;
    padding: 1px 7px;
    border-radius: 8px;
    font-size: 0.62rem;
    font-weight: 600;
    margin-left: 5px;
}

/* ── Cards ── */
.card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease;
    height: 100%;
}
.card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.07); }
.card-lg {
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
}

/* ── Briefing/List Card ── */
.brief-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 0.8rem 1.1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
}
.brief-left { flex: 1; }
.brief-title { font-size: 0.88rem; font-weight: 600; color: #111827; line-height: 1.3; }
.brief-meta { font-size: 0.75rem; color: #9ca3af; margin-top: 1px; }
.brief-desc { font-size: 0.8rem; color: #6b7280; margin-top: 3px; line-height: 1.5; }
.brief-right { min-width: 40px; text-align: right; padding-top: 2px; }

/* ── Tags ── */
.t {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    margin-right: 2px;
    vertical-align: middle;
}
.t-blue { background: #eff6ff; color: #2563eb; }
.t-purple { background: #f5f3ff; color: #7c3aed; }
.t-green { background: #ecfdf5; color: #059669; }
.t-amber { background: #fffbeb; color: #d97706; }
.t-red { background: #fef2f2; color: #dc2626; }
.t-gray { background: #f3f4f6; color: #6b7280; }
.t-sky { background: #f0f9ff; color: #0284c7; }

/* ── Relevance Bar ── */
.rel-bar-wrap { display: flex; align-items: center; gap: 6px; margin-top: 0.5rem; }
.rel-bar-track { flex: 1; height: 3px; background: #f3f4f6; border-radius: 2px; overflow: hidden; }
.rel-bar-fill { height: 100%; border-radius: 2px; }
.rel-bar-val { font-size: 0.72rem; font-weight: 700; min-width: 32px; text-align: right; }

/* ── Progress Fill Bar ── */
.fill-bar {
    height: 6px;
    background: #f3f4f6;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 4px;
}
.fill-bar-inner { height: 100%; border-radius: 3px; transition: width 0.4s ease; }

/* ── Pipeline (speaker status) ── */
.pipeline { display: flex; gap: 2px; margin-top: 8px; }
.pipe-step { flex: 1; height: 3px; background: #f3f4f6; border-radius: 2px; }
.pipe-step.active { background: #2563eb; }
.pipe-step.done { background: #059669; }
.pipe-label { font-size: 0.58rem; color: #9ca3af; margin-top: 2px; }

/* ── Phase Indicator ── */
.phase-bar { display: flex; gap: 1px; margin: 0.8rem 0; }
.phase-step {
    flex: 1; padding: 6px 8px;
    text-align: center; font-size: 0.6rem; font-weight: 600;
    color: #9ca3af; background: #f9fafb;
    letter-spacing: 0.3px; text-transform: uppercase;
}
.phase-step:first-child { border-radius: 6px 0 0 6px; }
.phase-step:last-child { border-radius: 0 6px 6px 0; }
.phase-step.active { background: #111827; color: #fff; }
.phase-step.done { background: #059669; color: #fff; }

/* ── Risk Badge ── */
.risk-low { color: #059669; }
.risk-medium { color: #d97706; }
.risk-high { color: #dc2626; }
.risk-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.risk-dot-low { background: #059669; }
.risk-dot-medium { background: #d97706; }
.risk-dot-high { background: #dc2626; }

/* ── Agenda Grid ── */
.agenda-slot {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-left: 3px solid #2563eb;
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 4px;
    font-size: 0.8rem;
}
.agenda-slot .time { font-size: 0.68rem; color: #9ca3af; font-weight: 500; }
.agenda-slot .title { font-weight: 600; color: #111827; margin-top: 1px; }
.agenda-slot .speaker { font-size: 0.72rem; color: #6b7280; }
.agenda-slot.keynote { border-left-color: #d97706; background: #fffbeb; }
.agenda-slot.panel { border-left-color: #7c3aed; }
.agenda-slot.break { border-left-color: #d1d5db; background: #f9fafb; }

/* ── Timeline ── */
.tl-item {
    display: flex; gap: 0.8rem; padding: 0.6rem 0;
    border-bottom: 1px solid #f3f4f6;
}
.tl-date { min-width: 70px; font-size: 0.72rem; font-weight: 600; color: #6b7280; }
.tl-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
.tl-dot.pending { background: #d1d5db; }
.tl-dot.in_progress { background: #2563eb; }
.tl-dot.completed { background: #059669; }
.tl-dot.overdue { background: #dc2626; }
.tl-content { flex: 1; }
.tl-title { font-size: 0.82rem; font-weight: 600; color: #111827; }
.tl-desc { font-size: 0.75rem; color: #9ca3af; }

/* ── Discussion ── */
.disc-msg {
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.3rem;
}
.disc-agent { font-size: 0.68rem; font-weight: 600; color: #6b7280; margin-bottom: 2px; }
.disc-text { font-size: 0.8rem; color: #374151; line-height: 1.5; }

/* ── Empty ── */
.empty { text-align: center; padding: 2.5rem; color: #d1d5db; font-size: 0.82rem; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    font-size: 0.8rem;
}

/* ── Comparison Table ── */
.cmp-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
}
.cmp-table th {
    background: #f9fafb;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    color: #6b7280;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #e5e7eb;
}
.cmp-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #f3f4f6;
    color: #374151;
}
.cmp-table tr:hover td { background: #f9fafb; }

/* ── Budget Bar ── */
.budget-row {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 0; border-bottom: 1px solid #f3f4f6;
}
.budget-cat { min-width: 100px; font-size: 0.75rem; font-weight: 600; color: #374151; }
.budget-bar { flex: 1; height: 8px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.budget-bar-fill { height: 100%; border-radius: 4px; }
.budget-amt { min-width: 80px; text-align: right; font-size: 0.75rem; font-weight: 600; color: #111827; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# API Helpers
# ============================================================

def api_get(path: str, params: dict | None = None) -> dict | list:
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return []

def api_post(path: str, data: dict) -> dict:
    try:
        r = httpx.post(f"{API_BASE}{path}", json=data, timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        st.error(f"API Error: {e}")
        return {}

def api_patch(path: str, data: dict) -> dict:
    try:
        r = httpx.patch(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        st.error(f"API Error: {e}")
        return {}

def api_delete(path: str) -> dict:
    try:
        r = httpx.delete(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return {}


def _sc(score: float) -> str:
    if score >= 0.85: return "#059669"
    if score >= 0.7: return "#2563eb"
    if score >= 0.5: return "#d97706"
    return "#dc2626"


def _pipe_idx(status: str) -> int:
    return {"candidate": 1, "shortlisted": 2, "contacting": 3, "confirmed": 4}.get(status, 0)


def _fmt_krw(amount: float) -> str:
    if amount >= 100_000_000:
        return f"{amount/100_000_000:.1f}억"
    if amount >= 10_000:
        return f"{amount/10_000:.0f}만"
    return f"{amount:,.0f}"


PERSONA = {
    "ai-tech-expert": ("AI Tech", "t-blue"),
    "enterprise-attendee": ("Enterprise", "t-purple"),
    "operations-manager": ("Ops", "t-amber"),
    "general-attendee": ("General", "t-green"),
}

CAT_COLORS = {
    "GenAI": ("t-purple", "#7c3aed"),
    "Enterprise AI": ("t-blue", "#2563eb"),
    "AI Infra": ("t-sky", "#0284c7"),
    "AI Policy": ("t-red", "#dc2626"),
    "Industry AI": ("t-amber", "#d97706"),
    "AI Research": ("t-green", "#059669"),
}

PHASE_ORDER = ["research", "planning", "outreach", "confirmation", "production", "event"]
PHASE_LABELS = {
    "research": "Research", "planning": "Planning", "outreach": "Outreach",
    "confirmation": "Confirm", "production": "Production", "event": "Event",
}

BUDGET_CAT_LABELS = {
    "speaker_fee": "Speaker Fees", "travel": "Travel", "venue": "Venue",
    "catering": "Catering", "production": "Production", "marketing": "Marketing",
    "staff": "Staff", "other": "Other",
}

BUDGET_CAT_COLORS = {
    "speaker_fee": "#2563eb", "travel": "#7c3aed", "venue": "#059669",
    "catering": "#d97706", "production": "#0284c7", "marketing": "#dc2626",
    "staff": "#6b7280", "other": "#9ca3af",
}


# ============================================================
# Data Loading
# ============================================================

suggestions = api_get("/suggestions", {"limit": 100})
trends = api_get("/trends")
speakers_data = api_get("/speakers", {"limit": 100, "sort": "overall_score"})
research_sessions = api_get("/research/sessions")
tracks = api_get("/tracks")
feedback_list = api_get("/feedback/history")
agenda_sessions = api_get("/agenda")
milestones_data = api_get("/milestones")
budget_items = api_get("/budget")
budget_summary = api_get("/budget/summary")
contacts_data = api_get("/contacts")
follow_up_alerts = api_get("/contacts/alerts")

for name in ("suggestions", "trends", "speakers_data", "research_sessions",
             "tracks", "feedback_list", "agenda_sessions", "milestones_data",
             "budget_items", "contacts_data", "follow_up_alerts"):
    if not isinstance(locals()[name], list):
        locals()[name] = []
if not isinstance(budget_summary, dict):
    budget_summary = {"total_estimated": 0, "total_actual": 0, "utilization": 0, "by_category": []}

pending = [s for s in suggestions if s.get("status") == "pending_review"]
sorted_trends = sorted(trends, key=lambda t: t.get("relevance_score") or 0, reverse=True)
sorted_speakers = sorted(speakers_data, key=lambda s: s.get("overall_score") or 0, reverse=True)


# ============================================================
# Header
# ============================================================

# D-day countdown
event_date = date(2026, 8, 15)
days_left = (event_date - date.today()).days

st.markdown(f"""
<div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
            <h1>AI SUMMIT AND EXPO 2026</h1>
            <div class="sub">{date.today().strftime('%B %d, %Y')} &middot; Conference Planning Intelligence</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:1.8rem;font-weight:800;color:#111827;line-height:1;">{days_left}</div>
            <div style="font-size:0.6rem;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;">Days Left</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ============================================================
# 5-Tab Structure
# ============================================================

tab_dash, tab_research, tab_agenda, tab_speakers, tab_plan = st.tabs([
    "Dashboard", "Research", "Agenda", "Speakers", "Plan"
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: DASHBOARD — Readiness Overview
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_dash:

    # ── Phase Indicator ──
    current_phase = "planning"
    if milestones_data:
        completed_phases = set()
        for m in milestones_data:
            if m.get("status") == "completed":
                completed_phases.add(m.get("phase"))
        for p in PHASE_ORDER:
            if p not in completed_phases:
                current_phase = p
                break

    phase_html = '<div class="phase-bar">'
    for p in PHASE_ORDER:
        cls = "done" if PHASE_ORDER.index(p) < PHASE_ORDER.index(current_phase) else ("active" if p == current_phase else "")
        phase_html += f'<div class="phase-step {cls}">{PHASE_LABELS[p]}</div>'
    phase_html += '</div>'
    st.markdown(phase_html, unsafe_allow_html=True)

    # ── KPI Strip ──
    n_trends = len(trends)
    n_speakers = len(speakers_data)
    n_confirmed = len([s for s in speakers_data if s.get("status") == "confirmed"])
    n_tracks = len(tracks)
    n_agenda = len(agenda_sessions)
    n_pending = len(pending)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, val, lbl in [
        (c1, n_trends, "Trends"), (c2, n_speakers, "Speakers"),
        (c3, n_confirmed, "Confirmed"), (c4, n_tracks, "Tracks"),
        (c5, n_agenda, "Sessions"), (c6, n_pending, "Pending"),
    ]:
        with col:
            st.markdown(f'<div class="kpi-item"><div class="kpi-num">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Readiness Gauges ──
    st.markdown('<div class="sec-title">Readiness</div>', unsafe_allow_html=True)

    target_keynote = 8
    target_track_speakers = 24
    target_tracks = 4
    target_sessions = 16

    tier1 = [s for s in speakers_data if s.get("tier") == "tier1_keynote"]
    tier3 = [s for s in speakers_data if s.get("tier") == "tier3_track"]
    confirmed_speakers = [s for s in speakers_data if s.get("status") == "confirmed"]

    gauges = [
        ("Keynote Pool", len(tier1), target_keynote, "#d97706"),
        ("Track Speakers", len(tier3), target_track_speakers, "#2563eb"),
        ("Confirmed", len(confirmed_speakers), target_keynote + target_track_speakers, "#059669"),
        ("Tracks", n_tracks, target_tracks, "#7c3aed"),
        ("Agenda Slots", n_agenda, target_sessions, "#0284c7"),
        ("Trends", n_trends, 20, "#dc2626"),
    ]

    gc = st.columns(6)
    for i, (label, current, target, color) in enumerate(gauges):
        pct = min(current / target * 100, 100) if target > 0 else 0
        with gc[i]:
            st.markdown(f"""
            <div class="kpi-item">
                <div style="font-size:0.65rem;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">{label}</div>
                <div style="font-size:1.1rem;font-weight:800;color:#111827;">{current}<span style="font-size:0.7rem;color:#9ca3af;font-weight:400;">/{target}</span></div>
                <div class="fill-bar"><div class="fill-bar-inner" style="width:{pct:.0f}%;background:{color};"></div></div>
            </div>
            """, unsafe_allow_html=True)

    # ── Risk Indicators ──
    high_risk = [s for s in speakers_data if s.get("risk_level") == "high"]
    medium_risk = [s for s in speakers_data if s.get("risk_level") == "medium"]
    overdue_milestones = [m for m in milestones_data if m.get("status") == "overdue"]
    no_response = [c for c in contacts_data if c.get("status") == "no_response"]

    risk_items = []
    if high_risk:
        risk_items.append(("high", f"{len(high_risk)} high-risk speaker(s)"))
    if overdue_milestones:
        risk_items.append(("high", f"{len(overdue_milestones)} overdue milestone(s)"))
    if no_response:
        risk_items.append(("medium", f"{len(no_response)} unanswered outreach(es)"))
    if medium_risk:
        risk_items.append(("medium", f"{len(medium_risk)} medium-risk speaker(s)"))
    if n_tracks < target_tracks:
        risk_items.append(("medium", f"Only {n_tracks}/{target_tracks} tracks defined"))
    if len(follow_up_alerts) > 0:
        risk_items.append(("medium", f"{len(follow_up_alerts)} follow-up(s) due"))

    if risk_items:
        st.markdown('<div class="sec-title">Risk Flags</div>', unsafe_allow_html=True)
        for level, msg in risk_items[:6]:
            dot_cls = f"risk-dot-{level}"
            text_cls = f"risk-{level}"
            st.markdown(f"""
            <div class="brief-card">
                <div class="brief-left">
                    <span class="risk-dot {dot_cls}"></span>
                    <span class="brief-title {text_cls}">{msg}</span>
                </div>
                <div class="brief-right"><span class="t t-{'red' if level == 'high' else 'amber'}">{level.upper()}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ── Upcoming Milestones ──
    if milestones_data:
        upcoming = [m for m in milestones_data if m.get("status") in ("pending", "in_progress", "overdue")][:5]
        if upcoming:
            st.markdown('<div class="sec-title">Upcoming Milestones</div>', unsafe_allow_html=True)
            for m in upcoming:
                status = m.get("status", "pending")
                due = m.get("due_date", "")
                days_until = (datetime.strptime(due, "%Y-%m-%d").date() - date.today()).days if due else 0
                due_text = f"D{'-' if days_until > 0 else '+'}{abs(days_until)}" if due else ""

                st.markdown(f"""
                <div class="tl-item">
                    <div class="tl-date">{due[:10] if due else ''}</div>
                    <div class="tl-dot {status}"></div>
                    <div class="tl-content">
                        <div class="tl-title">{m.get('title', '')}</div>
                        <div class="tl-desc">{m.get('description', '') or ''} · {m.get('owner', '') or ''}</div>
                    </div>
                    <div style="min-width:40px;text-align:right;">
                        <span class="t t-{'red' if days_until < 0 else 'amber' if days_until < 7 else 'gray'}">{due_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Pending Review ──
    if pending:
        st.markdown(f'<div class="sec-title">Pending Review<span class="sec-count">{len(pending)}</span></div>', unsafe_allow_html=True)
        for s in pending[:5]:
            is_trend = s.get("suggestion_type") == "trend"
            score = s.get("relevance_score") or 0
            sc = _sc(score)
            type_tag = '<span class="t t-blue">Trend</span>' if is_trend else '<span class="t t-purple">Speaker</span>'

            col_m, col_a = st.columns([7, 1])
            with col_m:
                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        {type_tag}
                        <span class="brief-title">{s['title']}</span>
                        <div class="brief-desc">{s.get('summary', '')[:120]}</div>
                    </div>
                    <div class="brief-right"><div class="rel-bar-val" style="color:{sc};">{score:.0%}</div></div>
                </div>
                """, unsafe_allow_html=True)
            with col_a:
                if st.button("Approve", key=f"ap_{s['id']}", use_container_width=True, type="primary"):
                    api_patch(f"/suggestions/{s['id']}/approve", {"status": "approved"})
                    st.rerun()
                if st.button("Dismiss", key=f"dm_{s['id']}", use_container_width=True):
                    api_patch(f"/suggestions/{s['id']}/dismiss", {"status": "dismissed"})
                    st.rerun()

    # ── Budget Overview (mini) ──
    if budget_summary.get("total_estimated", 0) > 0:
        st.markdown('<div class="sec-title">Budget Overview</div>', unsafe_allow_html=True)
        total_est = budget_summary.get("total_estimated", 0)
        total_act = budget_summary.get("total_actual", 0)
        util = budget_summary.get("utilization", 0)

        st.markdown(f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:0.75rem;font-weight:600;color:#374151;">Total Budget</span>
                <span style="font-size:0.75rem;font-weight:700;color:#111827;">{_fmt_krw(total_act)} / {_fmt_krw(total_est)}</span>
            </div>
            <div class="fill-bar" style="height:8px;">
                <div class="fill-bar-inner" style="width:{util*100:.0f}%;background:{'#059669' if util < 0.8 else '#d97706' if util < 1 else '#dc2626'};"></div>
            </div>
            <div style="font-size:0.65rem;color:#9ca3af;margin-top:3px;">{util:.0%} utilized</div>
        </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: RESEARCH — Trends + Commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_research:

    sub_trends, sub_run = st.tabs(["Trends", "Commands"])

    with sub_trends:
        if sorted_trends:
            categories = sorted(set(t.get("category", "") for t in sorted_trends if t.get("category")))
            cat_filter = st.selectbox("Category", ["All"] + categories, key="rt_cat")
            display_t = sorted_trends if cat_filter == "All" else [t for t in sorted_trends if t.get("category") == cat_filter]

            # Top 3 hero cards
            top3 = display_t[:3]
            cols = st.columns(3)
            for i, t in enumerate(top3):
                score = t.get("relevance_score") or 0
                cat = t.get("category", "")
                tag_cls, bar_color = CAT_COLORS.get(cat, ("t-gray", "#6b7280"))
                sc = _sc(score)
                with cols[i]:
                    st.markdown(f"""
                    <div class="card card-lg">
                        <div style="font-size:0.58rem;font-weight:800;color:#d1d5db;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.5rem;">#{i+1} Trending</div>
                        <div style="margin-bottom:5px;"><span class="t {tag_cls}">{cat}</span></div>
                        <div style="font-size:1rem;font-weight:700;color:#111827;line-height:1.3;">{t['keyword']}</div>
                        <div style="font-size:0.8rem;color:#6b7280;margin-top:4px;line-height:1.5;">{t.get('description', '')}</div>
                        <div class="rel-bar-wrap">
                            <div class="rel-bar-track"><div class="rel-bar-fill" style="width:{score*100:.0f}%;background:{bar_color};"></div></div>
                            <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Remaining as list
            for t in display_t[3:]:
                score = t.get("relevance_score") or 0
                cat = t.get("category", "")
                tag_cls, bar_color = CAT_COLORS.get(cat, ("t-gray", "#6b7280"))
                sc = _sc(score)

                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        <span class="t {tag_cls}">{cat}</span>
                        <span class="brief-title">{t['keyword']}</span>
                        <div class="brief-desc">{t.get('description', '')[:120]}{'...' if len(t.get('description',''))>120 else ''}</div>
                    </div>
                    <div class="brief-right"><div class="rel-bar-val" style="color:{sc};">{score:.0%}</div></div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Details", expanded=False):
                    ev = t.get("evidence", "")
                    if ev:
                        st.markdown(f"**Evidence:** {ev}")
                    src = t.get("source_conferences", "")
                    if src:
                        st.markdown(f"**Sources:** {src}")
                    sid = t.get("session_id")
                    if sid:
                        discs = api_get(f"/research/sessions/{sid}/discussions")
                        if isinstance(discs, list) and discs:
                            st.markdown("**Evaluations:**")
                            for d in discs:
                                a_lbl, a_cls = PERSONA.get(d.get("agent_name", ""), (d.get("agent_name", ""), "t-gray"))
                                st.markdown(f"""
                                <div class="disc-msg">
                                    <div class="disc-agent"><span class="t {a_cls}">{a_lbl}</span> {d.get('message_type','')}</div>
                                    <div class="disc-text">{d.get('content','')}</div>
                                </div>
                                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">No trends yet. Run a research scan to get started.</div>', unsafe_allow_html=True)

    with sub_run:
        st.markdown('<div class="sec-title">Research Commands</div>', unsafe_allow_html=True)

        c_r1, c_r2 = st.columns(2)
        with c_r1:
            st.markdown("**Trend Research**")
            tq = st.text_input("Keywords", placeholder="AI Agents, Edge AI...", key="cmd_tq")
            if st.button("Start", key="cmd_t", use_container_width=True, type="primary"):
                if tq:
                    r = api_post("/research/trends", {"query": tq})
                    if r.get("session_id"):
                        st.success(f"Session #{r['session_id']} started")
        with c_r2:
            st.markdown("**Speaker Search**")
            sq = st.text_input("Topic", placeholder="Agentic AI", key="cmd_sq")
            st_tier = st.selectbox("Tier", ["tier3_track", "tier1_keynote"], key="cmd_st",
                                   format_func=lambda x: "Track" if x == "tier3_track" else "Keynote")
            if st.button("Find", key="cmd_s", use_container_width=True, type="primary"):
                if sq:
                    r = api_post("/research/speakers", {"topic": sq, "tier": st_tier})
                    if r.get("session_id"):
                        st.success(f"Session #{r['session_id']} started")

        st.divider()
        c_sc, c_ev = st.columns(2)
        with c_sc:
            if st.button("Deep Research Scan", use_container_width=True):
                r = api_post("/suggestions/scan", {})
                if r.get("session_id"):
                    st.success(f"Scan #{r['session_id']}")
        with c_ev:
            if st.button("Planner Evaluation", use_container_width=True):
                r = api_post("/planner/evaluate", {})
                if r.get("session_id"):
                    st.success(f"Eval #{r['session_id']}")

        # Feedback
        st.divider()
        st.markdown('<div class="sec-title">Feedback</div>', unsafe_allow_html=True)
        fb = st.text_area("Content", height=70, key="fb_c", placeholder="Add feedback...")
        fb_t = st.selectbox("Type", ["general", "direction", "speaker", "trend", "track"], key="fb_t")
        if st.button("Submit", key="fb_s"):
            if fb:
                r = api_post("/feedback", {"content": fb, "feedback_type": fb_t})
                if r.get("id"):
                    st.success("Submitted")

        # Sessions
        st.divider()
        st.markdown('<div class="sec-title">Recent Sessions</div>', unsafe_allow_html=True)
        for s in (research_sessions or [])[:8]:
            stat = s.get("status", "")
            st_tag = {"running": '<span class="t t-amber">Running</span>', "completed": '<span class="t t-green">Done</span>', "failed": '<span class="t t-red">Failed</span>'}.get(stat, f'<span class="t t-gray">{stat}</span>')
            st.markdown(f"""
            <div class="brief-card">
                <div class="brief-left">
                    {st_tag} <span class="brief-title">{s.get('session_type','')}</span>
                    <span class="brief-meta">{s.get('input_query','')}</span>
                </div>
                <div class="brief-right"><span class="brief-meta">{s.get('created_at','')[:16]}</span></div>
            </div>
            """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: AGENDA — Session/Agenda Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_agenda:

    st.markdown('<div class="sec-title">Agenda Builder</div>', unsafe_allow_html=True)

    # Day selector
    day_sel = st.radio("Day", [1, 2], horizontal=True, key="agenda_day",
                       format_func=lambda x: f"Day {x} — {'Aug 15' if x == 1 else 'Aug 16'}")

    day_sessions = [s for s in agenda_sessions if s.get("day") == day_sel]

    # Build track map
    track_map = {t["id"]: t for t in tracks} if tracks else {}
    speaker_map = {s["id"]: s for s in speakers_data} if speakers_data else {}

    if day_sessions:
        # Group by track
        keynote_sessions = [s for s in day_sessions if s.get("session_type") == "keynote" or s.get("track_id") is None]
        track_sessions = {}
        for s in day_sessions:
            if s.get("track_id") and s.get("session_type") != "keynote":
                tid = s["track_id"]
                track_sessions.setdefault(tid, []).append(s)

        # Keynote row
        if keynote_sessions:
            st.markdown("**Keynote / Plenary**")
            for sess in sorted(keynote_sessions, key=lambda x: x.get("start_time", "")):
                sp_name = ""
                if sess.get("speaker_id") and sess["speaker_id"] in speaker_map:
                    sp = speaker_map[sess["speaker_id"]]
                    sp_name = f"{sp['name']} ({sp.get('organization', '')})"

                status_cls = {"confirmed": "t-green", "tentative": "t-amber", "draft": "t-gray", "cancelled": "t-red"}.get(sess.get("status", "draft"), "t-gray")

                st.markdown(f"""
                <div class="agenda-slot keynote">
                    <div class="time">{sess.get('start_time','')} – {sess.get('end_time','')}</div>
                    <div class="title">{sess.get('title','')}</div>
                    <div class="speaker">{sp_name}</div>
                    <span class="t {status_cls}">{sess.get('status','draft')}</span>
                </div>
                """, unsafe_allow_html=True)

        # Track columns
        if track_sessions:
            track_ids = sorted(track_sessions.keys())
            num_tracks = len(track_ids)
            cols = st.columns(num_tracks)
            for i, tid in enumerate(track_ids):
                track = track_map.get(tid, {})
                tc = TRACK_COLORS[i % len(TRACK_COLORS)]
                with cols[i]:
                    st.markdown(f"**<span style='color:{tc};'>{track.get('name', f'Track {tid}')}</span>**", unsafe_allow_html=True)
                    for sess in sorted(track_sessions[tid], key=lambda x: x.get("start_time", "")):
                        sp_name = ""
                        if sess.get("speaker_id") and sess["speaker_id"] in speaker_map:
                            sp = speaker_map[sess["speaker_id"]]
                            sp_name = sp["name"]

                        stype = sess.get("session_type", "presentation")
                        slot_cls = "panel" if stype == "panel" else ("break" if stype == "break" else "")

                        st.markdown(f"""
                        <div class="agenda-slot {slot_cls}" style="border-left-color:{tc};">
                            <div class="time">{sess.get('start_time','')} – {sess.get('end_time','')}</div>
                            <div class="title">{sess.get('title','')}</div>
                            <div class="speaker">{sp_name}</div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">No sessions for this day. Add your first session below.</div>', unsafe_allow_html=True)

    # Add session form
    st.divider()
    with st.expander("Add Session"):
        ac1, ac2 = st.columns(2)
        with ac1:
            a_title = st.text_input("Session Title", key="as_title")
            a_type = st.selectbox("Type", ["presentation", "keynote", "panel", "workshop", "break", "networking"], key="as_type")
            a_track = st.selectbox("Track", [None] + [t["id"] for t in tracks],
                                   format_func=lambda x: "Plenary" if x is None else track_map.get(x, {}).get("name", f"Track {x}"),
                                   key="as_track")
        with ac2:
            a_start = st.text_input("Start Time", placeholder="09:00", key="as_start")
            a_end = st.text_input("End Time", placeholder="09:45", key="as_end")
            a_speaker = st.selectbox("Speaker", [None] + [s["id"] for s in sorted_speakers],
                                     format_func=lambda x: "None" if x is None else f"{speaker_map.get(x, {}).get('name', '')} ({speaker_map.get(x, {}).get('organization', '')})",
                                     key="as_speaker")

        a_desc = st.text_area("Description", height=60, key="as_desc")

        if st.button("Add Session", key="as_btn", type="primary"):
            if a_title and a_start and a_end:
                data = {
                    "title": a_title, "day": day_sel, "start_time": a_start,
                    "end_time": a_end, "session_type": a_type,
                }
                if a_track:
                    data["track_id"] = a_track
                if a_speaker:
                    data["speaker_id"] = a_speaker
                if a_desc:
                    data["description"] = a_desc
                r = api_post("/agenda", data)
                if r.get("id"):
                    st.success(f"Session added (#{r['id']})")
                    st.rerun()

    # Export agenda
    if agenda_sessions:
        st.divider()
        st.markdown('<div class="sec-title">Export</div>', unsafe_allow_html=True)

        # Build CSV
        csv_lines = ["Day,Start,End,Type,Track,Title,Speaker,Status"]
        for s in sorted(agenda_sessions, key=lambda x: (x.get("day", 1), x.get("start_time", ""))):
            track_name = track_map.get(s.get("track_id"), {}).get("name", "Plenary")
            sp_name = speaker_map.get(s.get("speaker_id"), {}).get("name", "")
            csv_lines.append(f"{s.get('day','')},{s.get('start_time','')},{s.get('end_time','')},{s.get('session_type','')},{track_name},{s.get('title','')},{sp_name},{s.get('status','')}")

        csv_data = "\n".join(csv_lines)
        st.download_button("Download Agenda CSV", csv_data, "agenda.csv", "text/csv", key="dl_agenda")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: SPEAKERS — Full Management + Comparison
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_speakers:

    sub_list, sub_compare, sub_contacts_tab = st.tabs(["All Speakers", "Compare", "Communications"])

    # ── Speaker List ──
    with sub_list:
        if sorted_speakers:
            # Filters
            cf1, cf2, cf3, cf4 = st.columns(4)
            with cf1:
                tier_f = st.selectbox("Tier", ["All", "tier1_keynote", "tier3_track"], key="rs_tier",
                                      format_func=lambda x: {"All": "All", "tier1_keynote": "Keynote", "tier3_track": "Track"}.get(x, x))
            with cf2:
                stat_f = st.selectbox("Status", ["All", "candidate", "shortlisted", "contacting", "confirmed", "declined", "rejected"], key="rs_stat")
            with cf3:
                risk_f = st.selectbox("Risk", ["All", "low", "medium", "high"], key="rs_risk")
            with cf4:
                sort_f = st.selectbox("Sort", ["Score", "Name", "Risk"], key="rs_sort")

            disp = sorted_speakers[:]
            if tier_f != "All":
                disp = [s for s in disp if s.get("tier") == tier_f]
            if stat_f != "All":
                disp = [s for s in disp if s.get("status") == stat_f]
            if risk_f != "All":
                disp = [s for s in disp if s.get("risk_level") == risk_f]
            if sort_f == "Name":
                disp = sorted(disp, key=lambda s: s.get("name", ""))
            elif sort_f == "Risk":
                risk_order = {"high": 0, "medium": 1, "low": 2, None: 3}
                disp = sorted(disp, key=lambda s: risk_order.get(s.get("risk_level"), 3))

            # Speaker pipeline summary
            pipeline_counts = {}
            for s in speakers_data:
                st_val = s.get("status", "candidate")
                pipeline_counts[st_val] = pipeline_counts.get(st_val, 0) + 1

            pipe_cols = st.columns(6)
            pipe_statuses = ["candidate", "shortlisted", "contacting", "confirmed", "declined", "rejected"]
            pipe_colors = ["#6b7280", "#2563eb", "#d97706", "#059669", "#9ca3af", "#dc2626"]
            for i, (ps, pc) in enumerate(zip(pipe_statuses, pipe_colors)):
                with pipe_cols[i]:
                    cnt = pipeline_counts.get(ps, 0)
                    st.markdown(f'<div style="text-align:center;"><div style="font-size:1.1rem;font-weight:800;color:{pc};">{cnt}</div><div style="font-size:0.58rem;color:#9ca3af;text-transform:uppercase;">{ps}</div></div>', unsafe_allow_html=True)

            st.markdown("")

            # Card grid (3 cols)
            rows = [disp[i:i + 3] for i in range(0, len(disp), 3)]
            for row in rows:
                cols = st.columns(3)
                for i, sp in enumerate(row):
                    with cols[i]:
                        score = sp.get("overall_score") or 0
                        sc = _sc(score)
                        tier = sp.get("tier", "")
                        status = sp.get("status", "candidate")
                        sid = sp.get("id", 0)
                        risk = sp.get("risk_level", "low") or "low"

                        tier_tag = '<span class="t t-amber">Keynote</span>' if tier == "tier1_keynote" else '<span class="t t-sky">Track</span>' if tier == "tier3_track" else ""
                        risk_html = f'<span class="risk-dot risk-dot-{risk}"></span><span class="t t-{"red" if risk == "high" else "amber" if risk == "medium" else "green"}">{risk}</span>' if risk != "low" else ""

                        name_ko = sp.get("name_ko", "")
                        nk = f" ({name_ko})" if name_ko else ""
                        exp = sp.get("expertise", "")
                        if len(exp) > 70:
                            exp = exp[:70] + "..."
                        country = sp.get("country", "")

                        pipe = _pipe_idx(status)
                        pipe_html = '<div class="pipeline">'
                        for step in range(1, 5):
                            cls = "done" if step < pipe else ("active" if step == pipe else "")
                            pipe_html += f'<div class="pipe-step {cls}"></div>'
                        pipe_html += '</div>'
                        pipe_label = status.title()

                        fee = sp.get("estimated_fee")
                        fee_text = f" · {_fmt_krw(fee)}" if fee else ""

                        st.markdown(f"""
                        <div class="card">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                                <div style="font-size:0.9rem;font-weight:700;color:#111827;">{sp['name']}<span style="color:#9ca3af;font-size:0.78rem;font-weight:400;">{nk}</span></div>
                                <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                            </div>
                            <div style="font-size:0.75rem;color:#6b7280;">{sp.get('organization','')}{(' · ' + country) if country else ''}{fee_text}</div>
                            <div style="margin-top:5px;">{tier_tag} {risk_html}</div>
                            <div style="font-size:0.72rem;color:#9ca3af;margin-top:5px;line-height:1.4;">{exp}</div>
                            {pipe_html}
                            <div class="pipe-label">{pipe_label}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        with st.expander("Details", expanded=False):
                            parts = []
                            for lbl, key in [("Expertise", "expertise_score"), ("Name Value", "name_value_score"), ("Speaking", "speaking_score"), ("Relevance", "relevance_score")]:
                                v = sp.get(key) or 0
                                if v:
                                    parts.append(f"{lbl}: {v:.0%}")
                            if parts:
                                st.caption(" | ".join(parts))

                            bio = sp.get("bio", "")
                            if bio:
                                st.markdown(f"**Bio:** {bio}")
                            reason = sp.get("recommendation_reason", "")
                            if reason:
                                st.markdown(f"**Why:** {reason}")

                            # Contact history
                            sp_contacts = [c for c in contacts_data if c.get("speaker_id") == sid]
                            if sp_contacts:
                                st.markdown(f"**Contact History:** ({len(sp_contacts)} records)")
                                for c in sp_contacts[:3]:
                                    ct = c.get("contact_type", "")
                                    cst = c.get("status", "")
                                    st.caption(f"{c.get('contact_date', '')[:10]} · {ct} · {cst} — {c.get('subject', '')}")

                            # Discussions
                            sp_sid = sp.get("session_id")
                            if sp_sid:
                                discs = api_get(f"/research/sessions/{sp_sid}/discussions")
                                if isinstance(discs, list) and discs:
                                    st.markdown("**Evaluations:**")
                                    for d in discs:
                                        a_lbl, a_cls = PERSONA.get(d.get("agent_name", ""), (d.get("agent_name", ""), "t-gray"))
                                        st.markdown(f"""
                                        <div class="disc-msg">
                                            <div class="disc-agent"><span class="t {a_cls}">{a_lbl}</span></div>
                                            <div class="disc-text">{d.get('content','')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)

                            c_s1, c_s2 = st.columns(2)
                            with c_s1:
                                new_st = st.selectbox("Status",
                                    ["candidate", "shortlisted", "contacting", "confirmed", "declined", "rejected"],
                                    index=pipe_statuses.index(status) if status in pipe_statuses else 0,
                                    key=f"st_{sid}")
                            with c_s2:
                                new_risk = st.selectbox("Risk", ["low", "medium", "high"],
                                    index=["low", "medium", "high"].index(risk) if risk in ["low", "medium", "high"] else 0,
                                    key=f"rk_{sid}")
                            if st.button("Update", key=f"up_{sid}", use_container_width=True):
                                api_patch(f"/speakers/{sid}", {"status": new_st, "risk_level": new_risk})
                                st.rerun()
                st.markdown("")

            # Export speakers
            st.divider()
            csv_sp = ["Name,Organization,Country,Tier,Status,Score,Risk,Fee"]
            for sp in sorted_speakers:
                fee = sp.get("estimated_fee") or ""
                csv_sp.append(f"{sp.get('name','')},{sp.get('organization','')},{sp.get('country','')},{sp.get('tier','')},{sp.get('status','')},{sp.get('overall_score','')},{sp.get('risk_level','')},{fee}")
            st.download_button("Download Speakers CSV", "\n".join(csv_sp), "speakers.csv", "text/csv", key="dl_speakers")

        else:
            st.markdown('<div class="empty">No speakers yet.</div>', unsafe_allow_html=True)

    # ── Speaker Comparison ──
    with sub_compare:
        st.markdown('<div class="sec-title">Speaker Comparison Tool</div>', unsafe_allow_html=True)

        if sorted_speakers:
            compare_options = {s["id"]: f"{s['name']} ({s.get('organization', '')})" for s in sorted_speakers}
            selected_ids = st.multiselect(
                "Select speakers to compare (2-5)",
                options=list(compare_options.keys()),
                format_func=lambda x: compare_options.get(x, ""),
                max_selections=5,
                key="cmp_select",
            )

            if len(selected_ids) >= 2:
                cmp_speakers = [s for s in sorted_speakers if s["id"] in selected_ids]

                # Comparison table
                header = "<tr><th>Attribute</th>" + "".join(f"<th>{s['name']}</th>" for s in cmp_speakers) + "</tr>"

                rows_html = ""
                attrs = [
                    ("Organization", "organization"),
                    ("Country", "country"),
                    ("Tier", "tier"),
                    ("Status", "status"),
                    ("Overall Score", "overall_score"),
                    ("Expertise", "expertise_score"),
                    ("Name Value", "name_value_score"),
                    ("Speaking", "speaking_score"),
                    ("Relevance", "relevance_score"),
                    ("Risk", "risk_level"),
                    ("Fee", "estimated_fee"),
                ]
                for label, key in attrs:
                    cells = ""
                    for sp in cmp_speakers:
                        val = sp.get(key, "")
                        if key in ("overall_score", "expertise_score", "name_value_score", "speaking_score", "relevance_score") and val:
                            sc = _sc(val)
                            cells += f'<td><span style="color:{sc};font-weight:700;">{val:.0%}</span></td>'
                        elif key == "estimated_fee" and val:
                            cells += f"<td>{_fmt_krw(val)}</td>"
                        elif key == "risk_level" and val:
                            cells += f'<td><span class="risk-dot risk-dot-{val}"></span>{val}</td>'
                        elif key == "tier":
                            display = "Keynote" if val == "tier1_keynote" else "Track" if val == "tier3_track" else val or "-"
                            cells += f"<td>{display}</td>"
                        else:
                            cells += f"<td>{val or '-'}</td>"
                    rows_html += f"<tr><td style='font-weight:600;'>{label}</td>{cells}</tr>"

                st.markdown(f'<table class="cmp-table">{header}{rows_html}</table>', unsafe_allow_html=True)

                # Score radar (using bar chart since plotly may not be available)
                st.markdown('<div class="sec-title">Score Comparison</div>', unsafe_allow_html=True)
                score_keys = ["expertise_score", "name_value_score", "speaking_score", "relevance_score"]
                score_labels = ["Expertise", "Name Value", "Speaking", "Relevance"]

                for sp in cmp_speakers:
                    st.markdown(f"**{sp['name']}**")
                    for label, key in zip(score_labels, score_keys):
                        val = sp.get(key) or 0
                        sc = _sc(val)
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
                            <span style="min-width:80px;font-size:0.72rem;color:#6b7280;">{label}</span>
                            <div style="flex:1;height:4px;background:#f3f4f6;border-radius:2px;overflow:hidden;">
                                <div style="width:{val*100:.0f}%;height:100%;background:{sc};border-radius:2px;"></div>
                            </div>
                            <span style="font-size:0.72rem;font-weight:700;color:{sc};min-width:30px;text-align:right;">{val:.0%}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("")
            else:
                st.info("Select at least 2 speakers to compare.")
        else:
            st.markdown('<div class="empty">No speakers to compare.</div>', unsafe_allow_html=True)

    # ── Communications ──
    with sub_contacts_tab:
        st.markdown('<div class="sec-title">Communication Tracking</div>', unsafe_allow_html=True)

        # Follow-up alerts
        if follow_up_alerts:
            st.markdown(f'**Follow-up Alerts** ({len(follow_up_alerts)})')
            for alert in follow_up_alerts[:5]:
                st.markdown(f"""
                <div class="brief-card" style="border-left:3px solid #dc2626;">
                    <div class="brief-left">
                        <span class="t t-red">Follow Up</span>
                        <span class="brief-title">{alert.get('speaker_name', '')} ({alert.get('speaker_org', '')})</span>
                        <div class="brief-desc">{alert.get('subject', '')} — {alert.get('contact_type', '')}</div>
                    </div>
                    <div class="brief-right"><span class="brief-meta">{alert.get('follow_up_date', '')[:10]}</span></div>
                </div>
                """, unsafe_allow_html=True)
            st.divider()

        # Recent contacts
        if contacts_data:
            for c in contacts_data[:10]:
                sp = speaker_map.get(c.get("speaker_id"), {})
                dir_icon = "→" if c.get("direction") == "outbound" else "←"
                status_cls = {"replied": "t-green", "sent": "t-sky", "no_response": "t-amber", "follow_up_needed": "t-red"}.get(c.get("status", ""), "t-gray")

                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        <span class="t {status_cls}">{c.get('status', '')}</span>
                        <span class="brief-title">{dir_icon} {sp.get('name', 'Unknown')} — {c.get('subject', '')}</span>
                        <div class="brief-desc">{c.get('contact_type', '')} · {c.get('contacted_by', '')} · {c.get('contact_date', '')[:10]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">No contact records yet.</div>', unsafe_allow_html=True)

        # Add contact
        st.divider()
        with st.expander("Log New Contact"):
            cc1, cc2 = st.columns(2)
            with cc1:
                c_speaker = st.selectbox("Speaker", [s["id"] for s in sorted_speakers] if sorted_speakers else [],
                                         format_func=lambda x: speaker_map.get(x, {}).get("name", ""),
                                         key="cc_speaker")
                c_type = st.selectbox("Channel", ["email", "linkedin", "phone", "meeting", "other"], key="cc_type")
                c_dir = st.selectbox("Direction", ["outbound", "inbound"], key="cc_dir")
            with cc2:
                c_subject = st.text_input("Subject", key="cc_subject")
                c_by = st.text_input("Contacted by", key="cc_by")
                c_follow = st.text_input("Follow-up date", placeholder="2026-04-15", key="cc_follow")

            c_content = st.text_area("Notes", height=60, key="cc_content")

            if st.button("Log Contact", key="cc_btn", type="primary"):
                if c_speaker and c_subject:
                    data = {
                        "speaker_id": c_speaker, "contact_type": c_type,
                        "direction": c_dir, "subject": c_subject,
                        "contacted_by": c_by, "status": "sent",
                    }
                    if c_content:
                        data["content"] = c_content
                    if c_follow:
                        data["follow_up_date"] = c_follow
                    r = api_post("/contacts", data)
                    if r.get("id"):
                        st.success("Contact logged")
                        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5: PLAN — Tracks + Timeline + Budget
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_plan:

    sub_tracks, sub_timeline, sub_budget = st.tabs(["Tracks", "Timeline", "Budget"])

    # ── Tracks ──
    with sub_tracks:
        st.markdown(f'<div class="sec-title">Conference Tracks<span class="sec-count">{len(tracks)}</span></div>', unsafe_allow_html=True)

        if tracks:
            for idx, track in enumerate(tracks):
                tc = TRACK_COLORS[idx % len(TRACK_COLORS)]
                tid = track.get("id", 0)

                # Count speakers for this track
                trk_speakers = [s for s in speakers_data if s.get("track_id") == tid]
                trk_confirmed = [s for s in trk_speakers if s.get("status") == "confirmed"]
                trk_sessions = [s for s in agenda_sessions if s.get("track_id") == tid]

                st.markdown(f"""
                <div class="card" style="border-left:4px solid {tc};margin-bottom:0.8rem;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <div style="font-size:1rem;font-weight:700;color:#111827;">{track['name']}</div>
                            <div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">{track.get('description', '')}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.65rem;color:#9ca3af;text-transform:uppercase;">Speakers</div>
                            <div style="font-size:1rem;font-weight:700;color:#111827;">{len(trk_confirmed)}<span style="font-size:0.75rem;color:#9ca3af;">/{len(trk_speakers)}</span></div>
                        </div>
                    </div>
                    <div style="font-size:0.72rem;color:#9ca3af;margin-top:6px;">
                        <strong>Audience:</strong> {track.get('target_audience', '')} &middot;
                        <strong>Format:</strong> {track.get('session_format', '')} &middot;
                        <strong>Sessions:</strong> {len(trk_sessions)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if trk_speakers:
                    with st.expander(f"Assigned Speakers ({len(trk_speakers)})"):
                        for sp in trk_speakers:
                            sc = sp.get("overall_score") or 0
                            risk = sp.get("risk_level", "low") or "low"
                            risk_dot = f'<span class="risk-dot risk-dot-{risk}"></span>' if risk != "low" else ""
                            st.markdown(f"- {risk_dot}**{sp['name']}** ({sp.get('organization','')}) — {sc:.0%} · {sp.get('status', '')}")

            st.markdown("")
        else:
            st.markdown('<div class="empty">No tracks defined yet.</div>', unsafe_allow_html=True)

        with st.expander("Add New Track"):
            tn = st.text_input("Name", key="nt_n")
            td = st.text_area("Description", key="nt_d", height=50)
            ta = st.text_input("Audience", key="nt_a")
            tf = st.text_input("Format", key="nt_f", placeholder="Keynote 1 + Panel 2 + Case Study 2")
            if st.button("Create Track", key="nt_btn", type="primary"):
                if tn:
                    r = api_post("/tracks", {"name": tn, "description": td, "target_audience": ta, "session_format": tf})
                    if r.get("id"):
                        st.success(f"Created: {tn}")
                        st.rerun()

    # ── Timeline ──
    with sub_timeline:
        st.markdown('<div class="sec-title">Project Timeline</div>', unsafe_allow_html=True)

        # Phase filter
        phase_filter = st.selectbox("Phase", ["All"] + PHASE_ORDER, key="tl_phase",
                                    format_func=lambda x: PHASE_LABELS.get(x, x) if x != "All" else "All Phases")

        display_ms = milestones_data if phase_filter == "All" else [m for m in milestones_data if m.get("phase") == phase_filter]

        if display_ms:
            for m in display_ms:
                status = m.get("status", "pending")
                phase = m.get("phase", "")
                due = m.get("due_date", "")
                owner = m.get("owner", "")

                try:
                    days_until = (datetime.strptime(due, "%Y-%m-%d").date() - date.today()).days if due else 0
                except ValueError:
                    days_until = 0
                due_text = f"D{'-' if days_until > 0 else '+'}{abs(days_until)}" if due else ""

                phase_cls = {"research": "t-blue", "planning": "t-purple", "outreach": "t-amber", "confirmation": "t-green", "production": "t-sky", "event": "t-red"}.get(phase, "t-gray")
                status_cls = {"pending": "t-gray", "in_progress": "t-blue", "completed": "t-green", "overdue": "t-red", "skipped": "t-gray"}.get(status, "t-gray")

                st.markdown(f"""
                <div class="tl-item">
                    <div class="tl-date">{due[:10] if due else ''}</div>
                    <div class="tl-dot {status}"></div>
                    <div class="tl-content">
                        <div class="tl-title">{m.get('title', '')}</div>
                        <div class="tl-desc">
                            <span class="t {phase_cls}">{PHASE_LABELS.get(phase, phase)}</span>
                            <span class="t {status_cls}">{status}</span>
                            {f' · {owner}' if owner else ''}
                        </div>
                    </div>
                    <div style="min-width:40px;text-align:right;">
                        <span class="t t-{'red' if days_until < 0 else 'amber' if days_until < 7 else 'gray'}">{due_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">No milestones yet. Add your first milestone below.</div>', unsafe_allow_html=True)

        st.divider()
        with st.expander("Add Milestone"):
            mc1, mc2 = st.columns(2)
            with mc1:
                m_title = st.text_input("Title", key="ms_title")
                m_phase = st.selectbox("Phase", PHASE_ORDER, key="ms_phase",
                                       format_func=lambda x: PHASE_LABELS.get(x, x))
                m_owner = st.text_input("Owner", key="ms_owner")
            with mc2:
                m_due = st.text_input("Due Date", placeholder="2026-04-30", key="ms_due")
                m_desc = st.text_area("Description", height=60, key="ms_desc")

            if st.button("Add Milestone", key="ms_btn", type="primary"):
                if m_title and m_due:
                    data = {"title": m_title, "due_date": m_due, "phase": m_phase}
                    if m_desc:
                        data["description"] = m_desc
                    if m_owner:
                        data["owner"] = m_owner
                    r = api_post("/milestones", data)
                    if r.get("id"):
                        st.success(f"Milestone added")
                        st.rerun()

    # ── Budget ──
    with sub_budget:
        st.markdown('<div class="sec-title">Budget Tracking</div>', unsafe_allow_html=True)

        total_est = budget_summary.get("total_estimated", 0)
        total_act = budget_summary.get("total_actual", 0)
        util = budget_summary.get("utilization", 0)

        # Budget summary header
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.markdown(f'<div class="kpi-item"><div class="kpi-num">{_fmt_krw(total_est)}</div><div class="kpi-lbl">Estimated</div></div>', unsafe_allow_html=True)
        with bc2:
            st.markdown(f'<div class="kpi-item"><div class="kpi-num">{_fmt_krw(total_act)}</div><div class="kpi-lbl">Actual</div></div>', unsafe_allow_html=True)
        with bc3:
            bar_color = "#059669" if util < 0.8 else "#d97706" if util < 1 else "#dc2626"
            st.markdown(f"""
            <div class="kpi-item">
                <div class="kpi-num" style="color:{bar_color};">{util:.0%}</div>
                <div class="kpi-lbl">Utilized</div>
                <div class="fill-bar" style="margin-top:6px;"><div class="fill-bar-inner" style="width:{util*100:.0f}%;background:{bar_color};"></div></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Category breakdown
        by_cat = budget_summary.get("by_category", [])
        if by_cat:
            st.markdown('<div class="sec-title">By Category</div>', unsafe_allow_html=True)
            max_est = max((c.get("estimated", 0) for c in by_cat), default=1) or 1
            for cat_row in by_cat:
                cat = cat_row.get("category", "other")
                est = cat_row.get("estimated", 0)
                act = cat_row.get("actual", 0)
                pct = est / max_est * 100
                color = BUDGET_CAT_COLORS.get(cat, "#6b7280")

                st.markdown(f"""
                <div class="budget-row">
                    <div class="budget-cat">{BUDGET_CAT_LABELS.get(cat, cat)}</div>
                    <div class="budget-bar"><div class="budget-bar-fill" style="width:{pct:.0f}%;background:{color};"></div></div>
                    <div class="budget-amt">{_fmt_krw(est)}</div>
                </div>
                """, unsafe_allow_html=True)

        # Budget items list
        if budget_items:
            st.markdown("")
            for bi in budget_items[:15]:
                cat = bi.get("category", "other")
                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        <span class="t" style="background:{BUDGET_CAT_COLORS.get(cat, '#6b7280')}20;color:{BUDGET_CAT_COLORS.get(cat, '#6b7280')};">{BUDGET_CAT_LABELS.get(cat, cat)}</span>
                        <span class="brief-title">{bi.get('description', '')}</span>
                        <div class="brief-meta">{bi.get('status', '')} · {bi.get('currency', 'KRW')}</div>
                    </div>
                    <div class="brief-right" style="min-width:60px;">
                        <div style="font-size:0.8rem;font-weight:700;color:#111827;">{_fmt_krw(bi.get('estimated_amount', 0))}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Add budget item
        st.divider()
        with st.expander("Add Budget Item"):
            bb1, bb2 = st.columns(2)
            with bb1:
                b_cat = st.selectbox("Category",
                    ["speaker_fee", "travel", "venue", "catering", "production", "marketing", "staff", "other"],
                    format_func=lambda x: BUDGET_CAT_LABELS.get(x, x), key="bi_cat")
                b_desc = st.text_input("Description", key="bi_desc")
            with bb2:
                b_est = st.number_input("Estimated Amount (KRW)", min_value=0, step=100000, key="bi_est")
                b_sp = st.selectbox("Related Speaker", [None] + [s["id"] for s in sorted_speakers],
                                    format_func=lambda x: "None" if x is None else speaker_map.get(x, {}).get("name", ""),
                                    key="bi_sp")

            if st.button("Add Item", key="bi_btn", type="primary"):
                if b_desc and b_est > 0:
                    data = {"category": b_cat, "description": b_desc, "estimated_amount": b_est}
                    if b_sp:
                        data["speaker_id"] = b_sp
                    r = api_post("/budget", data)
                    if r.get("id"):
                        st.success("Budget item added")
                        st.rerun()

        # Export budget
        if budget_items:
            csv_budget = ["Category,Description,Estimated,Actual,Status,Currency"]
            for bi in budget_items:
                csv_budget.append(f"{bi.get('category','')},{bi.get('description','')},{bi.get('estimated_amount','')},{bi.get('actual_amount','')},{bi.get('status','')},{bi.get('currency','KRW')}")
            st.download_button("Download Budget CSV", "\n".join(csv_budget), "budget.csv", "text/csv", key="dl_budget")

    # Feedback History
    if feedback_list:
        st.divider()
        st.markdown(f'<div class="sec-title">Feedback History<span class="sec-count">{len(feedback_list)}</span></div>', unsafe_allow_html=True)
        for fb in feedback_list[:5]:
            st.markdown(f"""
            <div class="brief-card">
                <div class="brief-left">
                    <span class="t t-gray">{fb.get('feedback_type','')}</span>
                    <span class="brief-title">{fb.get('content','')[:100]}</span>
                </div>
                <div class="brief-right"><span class="brief-meta">{fb.get('created_at','')[:10]}</span></div>
            </div>
            """, unsafe_allow_html=True)
