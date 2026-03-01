"""AI SUMMIT 2026 — Conference Planning Intelligence.

Professional dashboard inspired by Luma, Exploding Topics, Feedly, Sessionboard.
3-tab structure: Today / Research / Plan
"""

import json
import os
from datetime import date

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
# CSS — Professional White Theme
# Inspired by: Luma (spacing/elegance), Exploding Topics (trend viz),
# Sessionboard (speaker pipeline), Feedly (intel dashboard)
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
    font-size: 0.85rem;
    color: #9ca3af;
    padding: 0.9rem 1.8rem;
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
    padding: 2rem 2.5rem 1.2rem 2.5rem;
    margin: -1rem -1rem 0 -1rem;
    border-bottom: 1px solid #e5e7eb;
}
.page-header h1 {
    font-size: 1.4rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    letter-spacing: -0.5px;
}
.page-header .sub {
    color: #9ca3af;
    font-size: 0.8rem;
    margin-top: 0.15rem;
    font-weight: 400;
}

/* ── KPI Strip ── */
.kpi-strip {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}
.kpi-item {
    flex: 1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.kpi-num {
    font-size: 1.8rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
}
.kpi-lbl {
    font-size: 0.65rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
    font-weight: 500;
}

/* ── Section ── */
.sec-title {
    font-size: 0.75rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 2rem 0 1rem 0;
}
.sec-count {
    display: inline-block;
    background: #f3f4f6;
    color: #6b7280;
    padding: 1px 7px;
    border-radius: 8px;
    font-size: 0.65rem;
    font-weight: 600;
    margin-left: 6px;
}

/* ── Hero Card (Top Trends/Speakers) ── */
.hero-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
    transition: box-shadow 0.2s ease, transform 0.15s ease;
    height: 100%;
}
.hero-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.hero-rank {
    font-size: 0.6rem;
    font-weight: 800;
    color: #d1d5db;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.hero-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.3;
    margin-bottom: 0.4rem;
}
.hero-desc {
    font-size: 0.82rem;
    color: #6b7280;
    line-height: 1.5;
}

/* ── Relevance Bar (Exploding Topics style) ── */
.rel-bar-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 0.8rem;
}
.rel-bar-track {
    flex: 1;
    height: 4px;
    background: #f3f4f6;
    border-radius: 2px;
    overflow: hidden;
}
.rel-bar-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
}
.rel-bar-val {
    font-size: 0.75rem;
    font-weight: 700;
    min-width: 36px;
    text-align: right;
}

/* ── Briefing Card ── */
.brief-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    transition: box-shadow 0.15s ease;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}
.brief-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.brief-left {
    flex: 1;
}
.brief-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: #111827;
    line-height: 1.35;
}
.brief-meta {
    font-size: 0.78rem;
    color: #9ca3af;
    margin-top: 2px;
}
.brief-desc {
    font-size: 0.82rem;
    color: #6b7280;
    margin-top: 4px;
    line-height: 1.5;
}
.brief-right {
    min-width: 44px;
    text-align: right;
    padding-top: 2px;
}

/* ── Tag System ── */
.t {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    margin-right: 3px;
    vertical-align: middle;
}
.t-blue { background: #eff6ff; color: #2563eb; }
.t-purple { background: #f5f3ff; color: #7c3aed; }
.t-green { background: #ecfdf5; color: #059669; }
.t-amber { background: #fffbeb; color: #d97706; }
.t-red { background: #fef2f2; color: #dc2626; }
.t-gray { background: #f3f4f6; color: #6b7280; }
.t-sky { background: #f0f9ff; color: #0284c7; }

/* ── Speaker Card ── */
.sp-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1.3rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.sp-card:hover {
    box-shadow: 0 4px 14px rgba(0,0,0,0.07);
}
.sp-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #111827;
}
.sp-org {
    font-size: 0.78rem;
    color: #6b7280;
    margin-top: 1px;
}
.sp-tags {
    margin-top: 8px;
}
.sp-expertise {
    font-size: 0.72rem;
    color: #9ca3af;
    margin-top: 8px;
    line-height: 1.4;
    flex: 1;
}

/* ── Pipeline (Sessionboard style) ── */
.pipeline {
    display: flex;
    gap: 2px;
    margin-top: 10px;
}
.pipe-step {
    flex: 1;
    height: 3px;
    background: #f3f4f6;
    border-radius: 2px;
}
.pipe-step.active {
    background: #2563eb;
}
.pipe-step.done {
    background: #059669;
}
.pipe-label {
    font-size: 0.6rem;
    color: #9ca3af;
    margin-top: 3px;
}

/* ── Track Card ── */
.trk-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}
.trk-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
}
.trk-name {
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 4px;
}
.trk-desc {
    font-size: 0.82rem;
    color: #6b7280;
    line-height: 1.5;
    margin-bottom: 8px;
}
.trk-meta {
    font-size: 0.72rem;
    color: #9ca3af;
}

/* ── Discussion ── */
.disc-msg {
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.4rem;
}
.disc-agent {
    font-size: 0.7rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 3px;
}
.disc-text {
    font-size: 0.82rem;
    color: #374151;
    line-height: 1.6;
}

/* ── Empty State ── */
.empty {
    text-align: center;
    padding: 3rem;
    color: #d1d5db;
    font-size: 0.85rem;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    font-size: 0.82rem;
}
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
    """Score color hex."""
    if score >= 0.85: return "#059669"
    if score >= 0.7: return "#2563eb"
    if score >= 0.5: return "#d97706"
    return "#dc2626"


def _pipe_status(status: str) -> int:
    """Pipeline step index: candidate=1, shortlisted=2, confirmed=3."""
    return {"candidate": 1, "shortlisted": 2, "confirmed": 3, "rejected": 0}.get(status, 0)


PERSONA = {
    "ai-tech-expert": ("AI Tech Expert", "t-blue"),
    "enterprise-attendee": ("Enterprise", "t-purple"),
    "operations-manager": ("Ops Manager", "t-amber"),
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


# ============================================================
# Data Loading
# ============================================================

suggestions = api_get("/suggestions", {"limit": 100})
trends = api_get("/trends")
speakers = api_get("/speakers", {"limit": 100, "sort": "overall_score"})
sessions = api_get("/research/sessions")
tracks = api_get("/tracks")
feedback_list = api_get("/feedback/history")

for name in ("suggestions", "trends", "speakers", "sessions", "tracks", "feedback_list"):
    if not isinstance(locals()[name], list):
        locals()[name] = []

pending = [s for s in suggestions if s.get("status") == "pending_review"]
sorted_trends = sorted(trends, key=lambda t: t.get("relevance_score") or 0, reverse=True)
sorted_speakers = sorted(speakers, key=lambda s: s.get("overall_score") or 0, reverse=True)


# ============================================================
# Header
# ============================================================

st.markdown(f"""
<div class="page-header">
    <h1>AI SUMMIT AND EXPO 2026</h1>
    <div class="sub">{date.today().strftime('%B %d, %Y')} &middot; Conference Planning Intelligence</div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ============================================================
# 3-Tab Structure
# ============================================================

tab_today, tab_research, tab_plan = st.tabs(["Today", "Research", "Plan"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: TODAY — Editorial Briefing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_today:

    # ── KPI Strip ──
    n_t = len(trends)
    n_s = len(speakers)
    n_tr = len(tracks)
    n_p = len(pending)
    n_done = len([s for s in sessions if s.get("status") == "completed"])

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl in [
        (c1, n_t, "Trends"), (c2, n_s, "Speakers"), (c3, n_tr, "Tracks"),
        (c4, n_p, "Pending"), (c5, n_done, "Sessions"),
    ]:
        with col:
            st.markdown(f'<div class="kpi-item"><div class="kpi-num">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    # ── Top Trends (Hero Cards — Flipboard/Exploding Topics style) ──
    st.markdown(f'<div class="sec-title">Top Trends<span class="sec-count">{n_t}</span></div>', unsafe_allow_html=True)

    if sorted_trends:
        top3 = sorted_trends[:3]
        cols = st.columns(3)
        for i, t in enumerate(top3):
            score = t.get("relevance_score") or 0
            cat = t.get("category", "")
            tag_cls, bar_color = CAT_COLORS.get(cat, ("t-gray", "#6b7280"))
            sc = _sc(score)
            with cols[i]:
                st.markdown(f"""
                <div class="hero-card">
                    <div class="hero-rank">#{i+1} Trending</div>
                    <div style="margin-bottom:6px;"><span class="t {tag_cls}">{cat}</span></div>
                    <div class="hero-title">{t['keyword']}</div>
                    <div class="hero-desc">{t.get('description', '')}</div>
                    <div class="rel-bar-wrap">
                        <div class="rel-bar-track">
                            <div class="rel-bar-fill" style="width:{score*100:.0f}%;background:{bar_color};"></div>
                        </div>
                        <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Remaining trends as compact list
        if len(sorted_trends) > 3:
            for t in sorted_trends[3:10]:
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
                    <div class="brief-right">
                        <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">No trends yet. Run a research scan to get started.</div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Top Speakers (Hero Cards) ──
    st.markdown(f'<div class="sec-title">Top Speakers<span class="sec-count">{n_s}</span></div>', unsafe_allow_html=True)

    if sorted_speakers:
        top3_sp = sorted_speakers[:3]
        cols = st.columns(3)
        for i, sp in enumerate(top3_sp):
            score = sp.get("overall_score") or 0
            tier = sp.get("tier", "")
            sc = _sc(score)
            tier_tag = '<span class="t t-amber">Keynote</span>' if tier == "tier1_keynote" else '<span class="t t-sky">Track</span>' if tier == "tier3_track" else ""
            name_ko = sp.get("name_ko", "")
            sub_name = f' ({name_ko})' if name_ko else ""
            exp = sp.get("expertise", "")
            if len(exp) > 80:
                exp = exp[:80] + "..."

            status = sp.get("status", "candidate")
            pipe = _pipe_status(status)
            pipe_html = '<div class="pipeline">'
            for step in range(1, 4):
                cls = "done" if step < pipe else ("active" if step == pipe else "")
                pipe_html += f'<div class="pipe-step {cls}"></div>'
            pipe_html += '</div>'
            pipe_label = {"candidate": "Candidate", "shortlisted": "Shortlisted", "confirmed": "Confirmed", "rejected": "Rejected"}.get(status, status)

            with cols[i]:
                st.markdown(f"""
                <div class="hero-card">
                    <div class="hero-rank">#{i+1} Speaker</div>
                    <div class="hero-title">{sp['name']}<span style="color:#9ca3af;font-weight:400;font-size:0.85rem;">{sub_name}</span></div>
                    <div style="font-size:0.8rem;color:#6b7280;">{sp.get('organization', '')}</div>
                    <div class="sp-tags" style="margin-top:6px;">{tier_tag}</div>
                    <div class="sp-expertise">{exp}</div>
                    <div class="rel-bar-wrap">
                        <div class="rel-bar-track">
                            <div class="rel-bar-fill" style="width:{score*100:.0f}%;background:{sc};"></div>
                        </div>
                        <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                    </div>
                    {pipe_html}
                    <div class="pipe-label">{pipe_label}</div>
                </div>
                """, unsafe_allow_html=True)

        # Remaining speakers as compact list
        if len(sorted_speakers) > 3:
            for sp in sorted_speakers[3:9]:
                score = sp.get("overall_score") or 0
                sc = _sc(score)
                tier = sp.get("tier", "")
                tier_tag = '<span class="t t-amber">Keynote</span>' if tier == "tier1_keynote" else '<span class="t t-sky">Track</span>' if tier == "tier3_track" else ""
                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        {tier_tag}
                        <span class="brief-title">{sp['name']}</span>
                        <span class="brief-meta">{sp.get('organization', '')}</span>
                    </div>
                    <div class="brief-right">
                        <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">No speakers yet.</div>', unsafe_allow_html=True)

    # ── Pending Review ──
    if pending:
        st.markdown(f'<div class="sec-title">Pending Review<span class="sec-count">{len(pending)}</span></div>', unsafe_allow_html=True)
        for s in pending[:8]:
            is_trend = s.get("suggestion_type") == "trend"
            score = s.get("relevance_score") or 0
            sc = _sc(score)
            type_tag = '<span class="t t-blue">Trend</span>' if is_trend else '<span class="t t-purple">Speaker</span>'
            high_tag = ' <span class="t t-red">High</span>' if score >= 0.8 else ""

            col_m, col_a = st.columns([7, 1])
            with col_m:
                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        {type_tag}{high_tag}
                        <span class="brief-title">{s['title']}</span>
                        <div class="brief-desc">{s.get('summary', '')[:150]}</div>
                    </div>
                    <div class="brief-right">
                        <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_a:
                if st.button("Approve", key=f"ap_{s['id']}", use_container_width=True, type="primary"):
                    api_patch(f"/suggestions/{s['id']}/approve", {"status": "approved"})
                    st.rerun()
                if st.button("Dismiss", key=f"dm_{s['id']}", use_container_width=True):
                    api_patch(f"/suggestions/{s['id']}/dismiss", {"status": "dismissed"})
                    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: RESEARCH — Deep Dive + Run Commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_research:

    sub_trends, sub_speakers, sub_run = st.tabs(["Trends", "Speakers", "Commands"])

    # ── Trends ──
    with sub_trends:
        if sorted_trends:
            categories = sorted(set(t.get("category", "") for t in sorted_trends if t.get("category")))
            cat_filter = st.selectbox("Category", ["All"] + categories, key="rt_cat")
            display = sorted_trends if cat_filter == "All" else [t for t in sorted_trends if t.get("category") == cat_filter]

            for t in display:
                score = t.get("relevance_score") or 0
                cat = t.get("category", "")
                tag_cls, bar_color = CAT_COLORS.get(cat, ("t-gray", "#6b7280"))
                sc = _sc(score)

                st.markdown(f"""
                <div class="brief-card">
                    <div class="brief-left">
                        <span class="t {tag_cls}">{cat}</span>
                        <span class="brief-title">{t['keyword']}</span>
                        <div class="brief-desc">{t.get('description', '')}</div>
                        <div class="rel-bar-wrap" style="max-width:300px;">
                            <div class="rel-bar-track"><div class="rel-bar-fill" style="width:{score*100:.0f}%;background:{bar_color};"></div></div>
                            <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Detail expander
                with st.expander(f"Details", expanded=False):
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

                    memo_k = f"mt_{t.get('id',0)}"
                    st.text_area("My Notes", value=st.session_state.get(memo_k, ""), key=memo_k, height=60, placeholder="Your notes...")
        else:
            st.markdown('<div class="empty">No trends yet.</div>', unsafe_allow_html=True)

    # ── Speakers ──
    with sub_speakers:
        if sorted_speakers:
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                tier_f = st.selectbox("Tier", ["All", "tier1_keynote", "tier3_track"], key="rs_tier",
                                      format_func=lambda x: {"All":"All","tier1_keynote":"Keynote","tier3_track":"Track"}.get(x,x))
            with cf2:
                stat_f = st.selectbox("Status", ["All", "candidate", "shortlisted", "confirmed", "rejected"], key="rs_stat")
            with cf3:
                sort_f = st.selectbox("Sort", ["Score", "Name"], key="rs_sort")

            disp = sorted_speakers[:]
            if tier_f != "All":
                disp = [s for s in disp if s.get("tier") == tier_f]
            if stat_f != "All":
                disp = [s for s in disp if s.get("status") == stat_f]
            if sort_f == "Name":
                disp = sorted(disp, key=lambda s: s.get("name", ""))

            # Card grid (3 cols)
            rows = [disp[i:i+3] for i in range(0, len(disp), 3)]
            for row in rows:
                cols = st.columns(3)
                for i, sp in enumerate(row):
                    with cols[i]:
                        score = sp.get("overall_score") or 0
                        sc = _sc(score)
                        tier = sp.get("tier", "")
                        status = sp.get("status", "candidate")
                        sid = sp.get("id", 0)

                        tier_tag = '<span class="t t-amber">Keynote</span>' if tier == "tier1_keynote" else '<span class="t t-sky">Track</span>' if tier == "tier3_track" else ""
                        status_tag = {"shortlisted":'<span class="t t-green">Shortlisted</span>',"confirmed":'<span class="t t-green">Confirmed</span>',"rejected":'<span class="t t-red">Rejected</span>'}.get(status, "")

                        name_ko = sp.get("name_ko", "")
                        nk = f" ({name_ko})" if name_ko else ""
                        exp = sp.get("expertise", "")
                        if len(exp) > 80:
                            exp = exp[:80] + "..."
                        country = sp.get("country", "")

                        pipe = _pipe_status(status)
                        pipe_html = '<div class="pipeline">'
                        for step in range(1, 4):
                            cls = "done" if step < pipe else ("active" if step == pipe else "")
                            pipe_html += f'<div class="pipe-step {cls}"></div>'
                        pipe_html += '</div>'

                        st.markdown(f"""
                        <div class="sp-card">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                                <div class="sp-name">{sp['name']}<span style="color:#9ca3af;font-size:0.8rem;font-weight:400;">{nk}</span></div>
                                <div class="rel-bar-val" style="color:{sc};">{score:.0%}</div>
                            </div>
                            <div class="sp-org">{sp.get('organization','')}{(' · ' + country) if country else ''}</div>
                            <div class="sp-tags">{tier_tag} {status_tag}</div>
                            <div class="sp-expertise">{exp}</div>
                            {pipe_html}
                        </div>
                        """, unsafe_allow_html=True)

                        with st.expander("Details", expanded=False):
                            # Scores
                            parts = []
                            for lbl, key in [("Expertise","expertise_score"),("Name Value","name_value_score"),("Speaking","speaking_score"),("Relevance","relevance_score")]:
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

                            # Discussions
                            sp_sid = sp.get("session_id")
                            if sp_sid:
                                discs = api_get(f"/research/sessions/{sp_sid}/discussions")
                                if isinstance(discs, list) and discs:
                                    st.markdown("**Evaluations:**")
                                    for d in discs:
                                        a_lbl, a_cls = PERSONA.get(d.get("agent_name",""), (d.get("agent_name",""), "t-gray"))
                                        st.markdown(f"""
                                        <div class="disc-msg">
                                            <div class="disc-agent"><span class="t {a_cls}">{a_lbl}</span></div>
                                            <div class="disc-text">{d.get('content','')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)

                            memo_k = f"ms_{sid}"
                            st.text_area("Notes", value=st.session_state.get(memo_k,""), key=memo_k, height=60, placeholder="Your notes...")

                            c_s1, c_s2 = st.columns(2)
                            with c_s1:
                                new_st = st.selectbox("Status", ["candidate","shortlisted","confirmed","rejected"],
                                    index=["candidate","shortlisted","confirmed","rejected"].index(status) if status in ["candidate","shortlisted","confirmed","rejected"] else 0,
                                    key=f"st_{sid}")
                            with c_s2:
                                if st.button("Update", key=f"up_{sid}", use_container_width=True):
                                    api_patch(f"/speakers/{sid}", {"status": new_st})
                                    st.rerun()
                st.markdown("")
        else:
            st.markdown('<div class="empty">No speakers yet.</div>', unsafe_allow_html=True)

    # ── Commands ──
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
            st_tier = st.selectbox("Tier", ["tier3_track","tier1_keynote"], key="cmd_st",
                                   format_func=lambda x: "Track" if x=="tier3_track" else "Keynote")
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
        fb = st.text_area("Content", height=80, key="fb_c", placeholder="Add feedback...")
        fb_t = st.selectbox("Type", ["general","direction","speaker","trend","track"], key="fb_t")
        if st.button("Submit", key="fb_s"):
            if fb:
                r = api_post("/feedback", {"content": fb, "feedback_type": fb_t})
                if r.get("id"):
                    st.success("Submitted")

        # Sessions
        st.divider()
        st.markdown('<div class="sec-title">Recent Sessions</div>', unsafe_allow_html=True)
        for s in (sessions or [])[:8]:
            stat = s.get("status","")
            st_tag = {"running":'<span class="t t-amber">Running</span>',"completed":'<span class="t t-green">Done</span>',"failed":'<span class="t t-red">Failed</span>'}.get(stat, f'<span class="t t-gray">{stat}</span>')
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
# TAB 3: PLAN — Tracks + Planning Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_plan:

    # ── Tracks (Sched-inspired color-coded grid) ──
    st.markdown(f'<div class="sec-title">Conference Tracks<span class="sec-count">{len(tracks)}</span></div>', unsafe_allow_html=True)

    if tracks:
        for idx, track in enumerate(tracks):
            tc = TRACK_COLORS[idx % len(TRACK_COLORS)]
            tid = track.get("id", 0)

            st.markdown(f"""
            <div class="trk-card" style="border-left:4px solid {tc};">
                <div class="trk-name">{track['name']}</div>
                <div class="trk-desc">{track.get('description', '')}</div>
                <div class="trk-meta">
                    <strong>Audience:</strong> {track.get('target_audience', '')} &middot;
                    <strong>Format:</strong> {track.get('session_format', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            trk_speakers = [s for s in speakers if s.get("track_id") == tid]
            if trk_speakers:
                with st.expander(f"Assigned Speakers ({len(trk_speakers)})"):
                    for sp in trk_speakers:
                        sc = sp.get("overall_score") or 0
                        st.markdown(f"- **{sp['name']}** ({sp.get('organization','')}) — {sc:.0%}")

            st.markdown("")
    else:
        st.markdown('<div class="empty">No tracks defined yet.</div>', unsafe_allow_html=True)

    # Add Track
    with st.expander("Add New Track"):
        tn = st.text_input("Name", key="nt_n")
        td = st.text_area("Description", key="nt_d", height=60)
        ta = st.text_input("Audience", key="nt_a")
        tf = st.text_input("Format", key="nt_f", placeholder="Keynote 1 + Panel 2 + Case Study 2")
        if st.button("Create", key="nt_btn"):
            if tn:
                r = api_post("/tracks", {"name": tn, "description": td, "target_audience": ta, "session_format": tf})
                if r.get("id"):
                    st.success(f"Created: {tn}")
                    st.rerun()

    st.divider()

    # ── Planning Summary ──
    st.markdown('<div class="sec-title">Planning Summary</div>', unsafe_allow_html=True)

    tier1 = [s for s in speakers if s.get("tier") == "tier1_keynote"]
    tier3 = [s for s in speakers if s.get("tier") == "tier3_track"]
    shortlisted = [s for s in speakers if s.get("status") == "shortlisted"]
    confirmed = [s for s in speakers if s.get("status") == "confirmed"]

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, len(tier1), "Keynote Pool"), (c2, len(tier3), "Track Pool"),
        (c3, len(shortlisted), "Shortlisted"), (c4, len(confirmed), "Confirmed"),
    ]:
        with col:
            st.markdown(f'<div class="kpi-item"><div class="kpi-num">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    # Feedback History
    if feedback_list:
        st.markdown(f'<div class="sec-title">Feedback<span class="sec-count">{len(feedback_list)}</span></div>', unsafe_allow_html=True)
        for fb in feedback_list[:8]:
            st.markdown(f"""
            <div class="brief-card">
                <div class="brief-left">
                    <span class="t t-gray">{fb.get('feedback_type','')}</span>
                    <span class="brief-title">{fb.get('content','')[:100]}</span>
                </div>
                <div class="brief-right"><span class="brief-meta">{fb.get('created_at','')[:10]}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # Planner Tasks
    planner_tasks = api_get("/planner/tasks")
    if isinstance(planner_tasks, list) and planner_tasks:
        st.markdown(f'<div class="sec-title">Planner Tasks<span class="sec-count">{len(planner_tasks)}</span></div>', unsafe_allow_html=True)
        for pt in planner_tasks:
            p = pt.get("priority", "")
            p_tag = '<span class="t t-red">High</span>' if p == "high" else f'<span class="t t-gray">{p}</span>'
            st.markdown(f"""
            <div class="brief-card">
                <div class="brief-left">
                    {p_tag} <span class="brief-title">{pt.get('task_type','')} — {pt.get('query','')}</span>
                    <div class="brief-desc">{pt.get('reason','')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
