"""AI SUMMIT 2026 — Professional Intelligence Dashboard.

실시간 AI 트렌드/연사 인텔리전스 대시보드.
딥리서치 기반 트렌드 분석, 연사 후보 제안, 기획자를 위한 뉴스 큐레이션.
"""

import json
import os
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st


# === 설정 ===

def _get_api_base() -> str:
    """환경변수 또는 Streamlit secrets에서 API URL 가져오기."""
    if os.environ.get("API_BASE_URL"):
        return os.environ["API_BASE_URL"]
    try:
        return st.secrets["API_BASE_URL"]
    except (KeyError, FileNotFoundError):
        return "http://localhost:8000/api"

API_BASE = _get_api_base()

st.set_page_config(
    page_title="AI SUMMIT 2026 — Intelligence Hub",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# === 프로페셔널 CSS ===

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* 전역 */
.stApp { background: #0a0a0f; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background: #0d0d14; border-right: 1px solid #1a1a2e; }
.stMarkdown { color: #c9d1d9; }

/* 메인 헤더 */
.main-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1a2e 100%);
    border: 1px solid #21262d;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e94560, #667eea, #00d2ff);
}
.main-header h1 {
    font-size: 2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #fff 0%, #a0aec0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header .tagline {
    color: #8b949e;
    font-size: 0.9rem;
    margin-top: 0.3rem;
    font-weight: 400;
}
.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(233,69,96,0.15);
    color: #e94560;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    margin-left: 12px;
    vertical-align: middle;
}
.live-dot {
    width: 8px; height: 8px;
    background: #e94560;
    border-radius: 50%;
    animation: livepulse 1.5s ease-in-out infinite;
}
@keyframes livepulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(233,69,96,0.4); }
    50% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(233,69,96,0); }
}

/* 섹션 헤더 */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #21262d;
}
.section-header h2 {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0;
}
.section-header .count-badge {
    background: #21262d;
    color: #8b949e;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* 인텔리전스 카드 */
.intel-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease;
}
.intel-card:hover {
    border-color: #388bfd;
    box-shadow: 0 0 20px rgba(56,139,253,0.1);
}
.intel-card.urgent {
    border-left: 3px solid #e94560;
}
.intel-card.trend {
    border-left: 3px solid #00d2ff;
}
.intel-card.speaker {
    border-left: 3px solid #667eea;
}
.intel-card.news {
    border-left: 3px solid #ffa657;
}

/* 태그 */
.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-right: 4px;
}
.tag-trend { background: rgba(0,210,255,0.15); color: #00d2ff; }
.tag-speaker { background: rgba(102,126,234,0.15); color: #667eea; }
.tag-urgent { background: rgba(233,69,96,0.15); color: #e94560; }
.tag-new { background: rgba(0,230,118,0.15); color: #00e676; }
.tag-auto { background: rgba(255,166,87,0.15); color: #ffa657; }
.tag-news { background: rgba(255,166,87,0.15); color: #ffa657; }

/* 스코어 시스템 */
.score-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px; height: 56px;
    border-radius: 50%;
    font-weight: 800;
    font-size: 1rem;
}
.score-bar-pro {
    height: 4px;
    background: #161b22;
    border-radius: 2px;
    overflow: hidden;
    margin: 3px 0;
}
.score-bar-fill-pro {
    height: 100%;
    border-radius: 2px;
}

/* KPI 카드 */
.kpi-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
}
.kpi-label {
    font-size: 0.7rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}
.kpi-delta {
    font-size: 0.75rem;
    margin-top: 4px;
}

/* 뉴스 피드 */
.news-item {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
}
.news-item:hover { border-color: #ffa657; }
.news-title {
    font-weight: 600;
    color: #e6edf3;
    font-size: 0.95rem;
    margin-bottom: 0.3rem;
}
.news-meta {
    font-size: 0.75rem;
    color: #8b949e;
}
.news-summary {
    font-size: 0.85rem;
    color: #b1bac4;
    margin-top: 0.4rem;
    line-height: 1.5;
}

/* 사이드바 */
.sidebar-section {
    background: #0d1117;
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}
.sidebar-kpi {
    text-align: center;
    padding: 0.5rem 0;
}
.sidebar-kpi .value {
    font-size: 1.5rem;
    font-weight: 800;
}
.sidebar-kpi .label {
    font-size: 0.65rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* 테이블 커스텀 */
.dataframe { font-size: 0.85rem !important; }

/* 숨김 요소 */
#MainMenu { visibility: hidden; }
header { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# === API 헬퍼 ===

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


def score_color(score: float) -> str:
    if score >= 0.8:
        return "#00e676"
    elif score >= 0.6:
        return "#ffa657"
    elif score >= 0.4:
        return "#f0883e"
    return "#f85149"


def score_bg(score: float) -> str:
    if score >= 0.8:
        return "rgba(0,230,118,0.12)"
    elif score >= 0.6:
        return "rgba(255,166,87,0.12)"
    elif score >= 0.4:
        return "rgba(240,136,62,0.12)"
    return "rgba(248,81,73,0.12)"


def parse_detail(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {}


def parse_urls(raw: str | None) -> list:
    if not raw:
        return []
    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# === 데이터 로딩 ===

suggestions = api_get("/suggestions", {"limit": 100})
trends = api_get("/trends")
speakers = api_get("/speakers", {"limit": 100, "sort": "overall_score"})
stats = api_get("/suggestions/stats")
sessions = api_get("/research/sessions")
feedback_list = api_get("/feedback/history")

pending = [s for s in suggestions if s.get("status") == "pending_review"] if isinstance(suggestions, list) else []
approved = [s for s in suggestions if s.get("status") == "approved"] if isinstance(suggestions, list) else []
recent_suggestions = sorted(suggestions, key=lambda x: x.get("created_at", ""), reverse=True)[:20] if isinstance(suggestions, list) else []


# ═══════════════════════════════════════════════════
# 사이드바 — 커맨드 센터
# ═══════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0;">
        <div style="font-size:1.3rem;font-weight:900;
             background:linear-gradient(135deg,#fff,#667eea);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            AI SUMMIT 2026
        </div>
        <div style="font-size:0.7rem;color:#8b949e;letter-spacing:2px;
             text-transform:uppercase;margin-top:2px;">
            Intelligence Hub
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 시스템 상태
    health = api_get("/health")
    is_online = isinstance(health, dict) and health.get("status") == "ok"
    running_sessions = [s for s in sessions if s.get("status") == "running"] if isinstance(sessions, list) else []

    status_color = "#00e676" if is_online else "#f85149"
    status_text = "SYSTEM ONLINE" if is_online else "OFFLINE"
    st.markdown(f"""
    <div class="sidebar-section" style="border-color:{status_color}22;">
        <div style="display:flex;align-items:center;gap:8px;justify-content:center;">
            <div style="width:8px;height:8px;border-radius:50%;background:{status_color};"></div>
            <span style="color:{status_color};font-size:0.75rem;font-weight:700;letter-spacing:1px;">{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI 그리드
    n_trends = len(trends) if isinstance(trends, list) else 0
    n_speakers = len(speakers) if isinstance(speakers, list) else 0
    n_pending = len(pending)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="sidebar-kpi"><div class="value" style="color:#00d2ff;">{n_trends}</div><div class="label">Trends</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="sidebar-kpi"><div class="value" style="color:#667eea;">{n_speakers}</div><div class="label">Speakers</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="sidebar-kpi"><div class="value" style="color:#e94560;">{n_pending}</div><div class="label">Pending</div></div>', unsafe_allow_html=True)

    # 실행 중인 에이전트
    if running_sessions:
        st.markdown(f"""
        <div class="sidebar-section" style="border-color:#00d2ff33;">
            <div style="display:flex;align-items:center;gap:6px;justify-content:center;">
                <div class="live-dot"></div>
                <span style="color:#00d2ff;font-size:0.75rem;font-weight:600;">
                    {len(running_sessions)} Agent(s) Running
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 액션 버튼
    st.markdown("##### ACTIONS")

    if st.button("🔍 Deep Research Scan", use_container_width=True, type="primary"):
        result = api_post("/suggestions/scan", {})
        if result.get("session_id"):
            st.success(f"Scan initiated (#{result['session_id']})")
            st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📊 Trend Research", use_container_width=True):
            st.session_state["show_trend_input"] = True
    with col_b:
        if st.button("🎤 Speaker Search", use_container_width=True):
            st.session_state["show_speaker_input"] = True

    # 수동 리서치 입력
    if st.session_state.get("show_trend_input"):
        with st.container():
            q = st.text_input("Research Keywords", placeholder="AI Agent, Multimodal AI, Edge AI", key="mq")
            if st.button("Start Research", key="run_t", use_container_width=True):
                if q:
                    r = api_post("/research/trends", {"query": q})
                    if r.get("session_id"):
                        st.success(f"Research started (#{r['session_id']})")
                        st.session_state["show_trend_input"] = False
                        st.rerun()

    if st.session_state.get("show_speaker_input"):
        with st.container():
            topic = st.text_input("Topic / Domain", placeholder="AI Agent", key="ms_topic")
            tier = st.selectbox("Tier", ["tier3_track", "tier1_keynote"], key="ms_tier")
            prefs = st.text_input("Preferences (optional)", key="ms_prefs")
            if st.button("Find Speakers", key="run_s", use_container_width=True):
                if topic:
                    r = api_post("/research/speakers", {
                        "topic": topic, "tier": tier,
                        "preferences": prefs or None,
                    })
                    if r.get("session_id"):
                        st.success(f"Search started (#{r['session_id']})")
                        st.session_state["show_speaker_input"] = False
                        st.rerun()

    st.divider()

    # 피드백
    with st.expander("💬 Submit Feedback"):
        fb = st.text_area("Content", height=80, key="fb_in",
                          placeholder="Need more healthcare AI speakers...")
        fb_type = st.selectbox("Type",
                               ["general", "direction", "speaker", "trend", "track"],
                               key="fb_t")
        if st.button("Submit", key="fb_sub", use_container_width=True):
            if fb:
                r = api_post("/feedback", {"content": fb, "feedback_type": fb_type})
                if r.get("id"):
                    st.success("Feedback submitted")

    st.divider()
    st.caption("v0.3.0 — Conference Intelligence Platform")


# ═══════════════════════════════════════════════════
# 메인 영역
# ═══════════════════════════════════════════════════

# 헤더
st.markdown("""
<div class="main-header">
    <h1>AI SUMMIT AND EXPO 2026
        <span class="live-indicator"><span class="live-dot"></span>LIVE INTELLIGENCE</span>
    </h1>
    <div class="tagline">
        Deep Research 기반 실시간 AI 트렌드 분석 · 연사 후보 발굴 · 기획자 인텔리전스
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# TAB 구조: Overview | Trends | Speakers | News | Activity
# ═══════════════════════════════════════════════════

tab_overview, tab_trends, tab_speakers, tab_news, tab_activity = st.tabs([
    "📋 Overview", "📊 Trend Intelligence", "🎤 Speaker Intelligence",
    "📰 News & Curation", "🤖 Agent Activity",
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: OVERVIEW — 핵심 현황 + 검토 대기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_overview:

    # KPI 대시보드
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    total_approved = len(approved)
    total_sessions = len(sessions) if isinstance(sessions, list) else 0
    completed_sessions = len([s for s in sessions if s.get("status") == "completed"]) if isinstance(sessions, list) else 0

    with kpi1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#00d2ff;">{n_trends}</div><div class="kpi-label">Active Trends</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#667eea;">{n_speakers}</div><div class="kpi-label">Speaker Candidates</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#e94560;">{n_pending}</div><div class="kpi-label">Pending Review</div></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#00e676;">{total_approved}</div><div class="kpi-label">Approved Today</div></div>', unsafe_allow_html=True)
    with kpi5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#ffa657;">{completed_sessions}</div><div class="kpi-label">Research Sessions</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # 검토 대기 항목
    if pending:
        st.markdown(f"""
        <div class="section-header">
            <h2>🔔 Pending Review</h2>
            <span class="count-badge">{len(pending)} items</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("AI 에이전트가 딥 리서치를 통해 자동 발굴한 항목입니다. 검토 후 승인/거절하세요.")

        for s in pending:
            detail = parse_detail(s.get("detail_json"))
            is_trend = s["suggestion_type"] == "trend"
            score = s.get("relevance_score") or 0
            sc = score_color(score)
            card_class = "trend" if is_trend else "speaker"

            col_main, col_score, col_act = st.columns([5, 1, 1])

            with col_main:
                tag_html = f'<span class="tag tag-{"trend" if is_trend else "speaker"}">{"TREND" if is_trend else "SPEAKER"}</span>'
                tag_html += '<span class="tag tag-new">NEW</span>'
                if s.get("relevance_score", 0) >= 0.8:
                    tag_html += '<span class="tag tag-urgent">HIGH RELEVANCE</span>'

                st.markdown(f"""
                <div class="intel-card {card_class}">
                    <div style="margin-bottom:8px;">{tag_html}</div>
                    <div style="font-size:1.1rem;font-weight:700;color:#e6edf3;margin-bottom:6px;">
                        {s['title']}
                    </div>
                """, unsafe_allow_html=True)

                if is_trend:
                    if s.get("summary"):
                        st.markdown(f'<div style="color:#b1bac4;font-size:0.9rem;line-height:1.6;">{s["summary"]}</div>', unsafe_allow_html=True)
                    cat = detail.get("category", "")
                    why = detail.get("why_new", "")
                    if cat:
                        st.markdown(f'<span style="color:#8b949e;font-size:0.8rem;">Category: {cat}</span>', unsafe_allow_html=True)
                    if why:
                        st.markdown(f'<div style="color:#00d2ff;font-size:0.85rem;margin-top:4px;">💡 {why}</div>', unsafe_allow_html=True)
                else:
                    org = detail.get("organization", "")
                    title_str = detail.get("title", "")
                    why = detail.get("why_trending", "") or detail.get("why_new", "")
                    tier = detail.get("suggested_tier", "")

                    meta_parts = []
                    if title_str:
                        meta_parts.append(title_str)
                    if org:
                        meta_parts.append(f"@ {org}")
                    if tier:
                        tier_label = {"tier1_keynote": "🏆 Keynote", "tier3_track": "📌 Track"}.get(tier, tier)
                        meta_parts.append(tier_label)

                    if meta_parts:
                        st.markdown(f'<div style="color:#8b949e;font-size:0.85rem;">{" · ".join(meta_parts)}</div>', unsafe_allow_html=True)
                    if s.get("summary"):
                        st.markdown(f'<div style="color:#b1bac4;font-size:0.9rem;line-height:1.6;margin-top:4px;">{s["summary"]}</div>', unsafe_allow_html=True)
                    if why:
                        st.markdown(f'<div style="color:#667eea;font-size:0.85rem;margin-top:4px;">💡 {why}</div>', unsafe_allow_html=True)
                    if detail.get("linkedin_url"):
                        st.markdown(f'[🔗 LinkedIn Profile]({detail["linkedin_url"]})')

                # 소스 링크
                urls = parse_urls(s.get("source_urls"))
                if urls:
                    with st.expander("📎 Sources"):
                        for u in urls[:5]:
                            st.markdown(f"- {u}")

                st.markdown('</div>', unsafe_allow_html=True)

            with col_score:
                st.markdown(f"""
                <div style="text-align:center;padding-top:1.5rem;">
                    <div class="score-circle" style="background:{score_bg(score)};border:2px solid {sc};color:{sc};">
                        {score:.0%}
                    </div>
                    <div style="color:#8b949e;font-size:0.65rem;margin-top:4px;">RELEVANCE</div>
                </div>
                """, unsafe_allow_html=True)

            with col_act:
                st.markdown("<div style='padding-top:1.2rem;'></div>", unsafe_allow_html=True)
                if st.button("✅ Approve", key=f"ap_{s['id']}", use_container_width=True, type="primary"):
                    api_patch(f"/suggestions/{s['id']}/approve", {"status": "approved"})
                    st.rerun()
                if st.button("❌ Dismiss", key=f"dm_{s['id']}", use_container_width=True):
                    api_patch(f"/suggestions/{s['id']}/dismiss", {"status": "dismissed"})
                    st.rerun()

    else:
        st.markdown("""
        <div class="intel-card" style="text-align:center;padding:2rem;">
            <div style="font-size:1.2rem;color:#8b949e;margin-bottom:0.5rem;">
                No pending items
            </div>
            <div style="font-size:0.85rem;color:#484f58;">
                사이드바의 "Deep Research Scan" 버튼으로 AI 에이전트를 실행하세요.
                <br>에이전트가 최신 AI 트렌드와 연사 후보를 자동으로 발굴합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 최근 활동 타임라인
    st.markdown("""
    <div class="section-header" style="margin-top:2rem;">
        <h2>⚡ Recent Intelligence Feed</h2>
    </div>
    """, unsafe_allow_html=True)

    if recent_suggestions:
        for s in recent_suggestions[:10]:
            detail = parse_detail(s.get("detail_json"))
            is_trend = s["suggestion_type"] == "trend"
            status = s.get("status", "")
            score = s.get("relevance_score") or 0

            status_badge = {
                "pending_review": '<span class="tag tag-urgent">PENDING</span>',
                "approved": '<span class="tag tag-new">APPROVED</span>',
                "dismissed": '<span class="tag" style="background:rgba(139,148,158,0.15);color:#8b949e;">DISMISSED</span>',
            }.get(status, "")

            type_badge = f'<span class="tag tag-{"trend" if is_trend else "speaker"}">{"TREND" if is_trend else "SPEAKER"}</span>'

            created = s.get("created_at", "")[:16]

            st.markdown(f"""
            <div class="news-item">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        {type_badge} {status_badge}
                        <span class="news-title" style="margin-left:4px;">{s['title']}</span>
                    </div>
                    <span style="color:{score_color(score)};font-weight:700;font-size:0.85rem;">{score:.0%}</span>
                </div>
                <div class="news-meta">{created}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("아직 인텔리전스 피드가 없습니다. Deep Research Scan을 실행해주세요.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: TREND INTELLIGENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_trends:

    if isinstance(trends, list) and trends:
        # 트렌드 메트릭 카드
        sorted_trends = sorted(trends, key=lambda t: t.get("relevance_score") or 0, reverse=True)
        top_n = min(6, len(sorted_trends))
        cols = st.columns(top_n)

        for i, t in enumerate(sorted_trends[:top_n]):
            score = t.get("relevance_score") or 0
            sc = score_color(score)
            auto_badge = ' <span class="tag tag-auto">AI</span>' if t.get("is_auto_discovered") else ""
            with cols[i]:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value" style="color:{sc};">{score:.0%}</div>
                    <div class="kpi-label">{t['keyword']}{auto_badge}</div>
                    <div style="color:#484f58;font-size:0.7rem;">{t.get('category', '')}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")

        # 트렌드 상세 카드
        st.markdown(f"""
        <div class="section-header">
            <h2>Trend Analysis</h2>
            <span class="count-badge">{len(trends)} tracked</span>
        </div>
        """, unsafe_allow_html=True)

        for t in sorted_trends:
            score = t.get("relevance_score") or 0
            sc = score_color(score)
            auto = '<span class="tag tag-auto">AUTO-DISCOVERED</span>' if t.get("is_auto_discovered") else ""

            with st.container():
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
                    <div class="intel-card trend">
                        <div style="margin-bottom:6px;">
                            <span class="tag tag-trend">{t.get('category', 'TREND')}</span>
                            {auto}
                        </div>
                        <div style="font-size:1.1rem;font-weight:700;color:#e6edf3;">{t['keyword']}</div>
                        <div style="color:#b1bac4;font-size:0.9rem;margin-top:6px;line-height:1.6;">
                            {t.get('description', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 근거 자료
                    evidence = t.get("evidence")
                    if evidence:
                        ev_list = parse_urls(evidence) if isinstance(evidence, str) else (evidence if isinstance(evidence, list) else [])
                        if ev_list:
                            with st.expander("📎 Evidence & Sources"):
                                for ev in ev_list:
                                    if isinstance(ev, dict):
                                        src = ev.get("source", "")
                                        url = ev.get("url", "")
                                        snippet = ev.get("snippet", "")
                                        if url:
                                            st.markdown(f"- [{src}]({url}): {snippet}")
                                        else:
                                            st.markdown(f"- {src}: {snippet}")
                                    else:
                                        st.markdown(f"- {ev}")

                with c2:
                    st.markdown(f"""
                    <div style="text-align:center;padding-top:1rem;">
                        <div class="score-circle" style="background:{score_bg(score)};border:2px solid {sc};color:{sc};">
                            {score:.0%}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # 카테고리 분포 차트
        df = pd.DataFrame(trends)
        if "category" in df.columns:
            cat_counts = df["category"].value_counts()
            if not cat_counts.empty:
                st.markdown("""
                <div class="section-header">
                    <h2>Category Distribution</h2>
                </div>
                """, unsafe_allow_html=True)
                st.bar_chart(cat_counts, height=250)

    else:
        st.markdown("""
        <div class="intel-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">📊</div>
            <div style="font-size:1.1rem;color:#8b949e;">No trend data yet</div>
            <div style="font-size:0.85rem;color:#484f58;margin-top:0.5rem;">
                Deep Research Scan을 실행하면 AI 에이전트가 최신 AI 트렌드를 자동 분석합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: SPEAKER INTELLIGENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_speakers:

    if isinstance(speakers, list) and speakers:
        # 필터 바
        fc1, fc2, fc3 = st.columns([1, 1, 3])
        with fc1:
            f_tier = st.selectbox("Tier", ["All", "tier1_keynote", "tier3_track", "unassigned"], key="ft")
        with fc2:
            f_status = st.selectbox("Status", ["All", "candidate", "shortlisted", "contacting", "confirmed", "declined"], key="fs")
        with fc3:
            f_search = st.text_input("🔍 Search", placeholder="Name, organization, keyword...", key="fsearch")

        filtered = speakers
        if f_tier != "All":
            filtered = [s for s in filtered if s.get("tier") == f_tier]
        if f_status != "All":
            filtered = [s for s in filtered if s.get("status") == f_status]
        if f_search:
            q = f_search.lower()
            filtered = [
                s for s in filtered
                if q in (s.get("name") or "").lower()
                or q in (s.get("organization") or "").lower()
                or q in (s.get("recommendation_reason") or "").lower()
            ]

        # 통계 바
        confirmed = len([s for s in speakers if s.get("status") == "confirmed"])
        shortlisted = len([s for s in speakers if s.get("status") == "shortlisted"])
        contacting = len([s for s in speakers if s.get("status") == "contacting"])

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#667eea;">{len(filtered)}</div><div class="kpi-label">Showing</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#00e676;">{confirmed}</div><div class="kpi-label">Confirmed</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#ffa657;">{shortlisted}</div><div class="kpi-label">Shortlisted</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#00d2ff;">{contacting}</div><div class="kpi-label">Contacting</div></div>', unsafe_allow_html=True)

        st.markdown("")

        # 연사 카드
        for sp in filtered:
            overall = sp.get("overall_score") or 0
            sc = score_color(overall)
            auto = '<span class="tag tag-auto">AI DISCOVERED</span>' if sp.get("is_auto_discovered") else ""

            tier_map = {"tier1_keynote": ("🏆", "KEYNOTE"), "tier3_track": ("📌", "TRACK")}
            tier_icon, tier_label = tier_map.get(sp.get("tier"), ("⬜", "UNASSIGNED"))

            status_colors = {
                "confirmed": "#00e676", "shortlisted": "#ffa657",
                "contacting": "#00d2ff", "candidate": "#8b949e",
                "declined": "#f85149", "rejected": "#f85149",
            }
            st_color = status_colors.get(sp.get("status"), "#8b949e")

            c_info, c_scores, c_ctrl = st.columns([4, 2, 1])

            with c_info:
                st.markdown(f"""
                <div class="intel-card speaker">
                    <div style="margin-bottom:6px;">
                        <span class="tag tag-speaker">{tier_label}</span>
                        <span class="tag" style="background:{st_color}22;color:{st_color};">{sp.get('status', 'candidate').upper()}</span>
                        {auto}
                    </div>
                    <div style="font-size:1.15rem;font-weight:700;color:#e6edf3;">
                        {tier_icon} {sp['name']}
                    </div>
                    <div style="color:#8b949e;font-size:0.85rem;margin-top:2px;">
                        {sp.get('title', '')} @ {sp.get('organization', 'N/A')} · {sp.get('country', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if sp.get("recommendation_reason"):
                    st.markdown(f'<div style="color:#b1bac4;font-size:0.85rem;line-height:1.5;margin-top:-0.5rem;padding:0 1.5rem 1rem;">{sp["recommendation_reason"][:200]}</div>', unsafe_allow_html=True)

                links = []
                if sp.get("linkedin_url"):
                    links.append(f"[LinkedIn]({sp['linkedin_url']})")
                if sp.get("website_url"):
                    links.append(f"[Website]({sp['website_url']})")
                if links:
                    st.markdown(" · ".join(links))

            with c_scores:
                st.markdown(f"""
                <div style="text-align:center;padding-top:0.8rem;">
                    <div class="score-circle" style="width:64px;height:64px;font-size:1.2rem;
                         background:{score_bg(overall)};border:2px solid {sc};color:{sc};">
                        {overall:.0%}
                    </div>
                    <div style="color:#8b949e;font-size:0.65rem;margin-top:4px;">OVERALL</div>
                </div>
                """, unsafe_allow_html=True)

                score_items = [
                    ("Expertise", sp.get("expertise_score") or 0),
                    ("Name Value", sp.get("name_value_score") or 0),
                    ("Speaking", sp.get("speaking_score") or 0),
                    ("Relevance", sp.get("relevance_score") or 0),
                ]
                for lbl, val in score_items:
                    vc = score_color(val)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
                        <span style="color:#8b949e;font-size:0.65rem;width:55px;">{lbl}</span>
                        <div class="score-bar-pro" style="flex:1;">
                            <div class="score-bar-fill-pro" style="width:{val*100:.0f}%;background:{vc};"></div>
                        </div>
                        <span style="color:{vc};font-size:0.7rem;font-weight:600;">{val:.0%}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with c_ctrl:
                st.markdown("<div style='padding-top:0.5rem;'></div>", unsafe_allow_html=True)
                statuses = ["candidate", "shortlisted", "contacting", "confirmed", "declined", "rejected"]
                current = sp.get("status", "candidate")
                idx = statuses.index(current) if current in statuses else 0
                new_st = st.selectbox("Status", statuses, index=idx, key=f"st_{sp['id']}", label_visibility="collapsed")
                if new_st != current:
                    api_patch(f"/speakers/{sp['id']}", {"status": new_st})
                    st.rerun()

            st.markdown("<div style='border-bottom:1px solid #21262d;margin:0.5rem 0;'></div>", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="intel-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">🎤</div>
            <div style="font-size:1.1rem;color:#8b949e;">No speaker data yet</div>
            <div style="font-size:0.85rem;color:#484f58;margin-top:0.5rem;">
                Deep Research Scan을 실행하면 AI 에이전트가 연사 후보를 자동 발굴합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: NEWS & CURATION — 기획자를 위한 뉴스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_news:

    st.markdown("""
    <div class="section-header">
        <h2>📰 Conference Planner Intelligence</h2>
    </div>
    """, unsafe_allow_html=True)
    st.caption("AI 에이전트가 수집한 트렌드/연사 정보를 기획자 관점에서 큐레이션합니다.")

    # 트렌드 기반 뉴스 큐레이션
    curated_trends = sorted(
        [s for s in suggestions if s.get("suggestion_type") == "trend"] if isinstance(suggestions, list) else [],
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )
    curated_speakers = sorted(
        [s for s in suggestions if s.get("suggestion_type") == "speaker"] if isinstance(suggestions, list) else [],
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )

    col_news, col_picks = st.columns([3, 2])

    with col_news:
        st.markdown("##### 🔥 Latest AI Trend Insights")

        if curated_trends:
            for item in curated_trends[:10]:
                detail = parse_detail(item.get("detail_json"))
                score = item.get("relevance_score") or 0
                sc = score_color(score)
                status = item.get("status", "")
                created = item.get("created_at", "")[:10]
                urls = parse_urls(item.get("source_urls"))

                status_badge = {
                    "approved": "✅",
                    "pending_review": "🔔",
                    "dismissed": "⏭️",
                }.get(status, "")

                st.markdown(f"""
                <div class="news-item">
                    <div style="display:flex;justify-content:space-between;align-items:start;">
                        <div style="flex:1;">
                            <div class="news-title">{status_badge} {item['title']}</div>
                            <div class="news-meta">
                                {created} · Relevance: <span style="color:{sc};font-weight:600;">{score:.0%}</span>
                                {f" · Category: {detail.get('category', '')}" if detail.get('category') else ""}
                            </div>
                            <div class="news-summary">{item.get('summary', '')}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if urls:
                    with st.expander(f"Sources ({len(urls)})"):
                        for u in urls[:5]:
                            st.markdown(f"- {u}")
        else:
            st.info("아직 트렌드 뉴스가 없습니다. Deep Research Scan을 실행해주세요.")

    with col_picks:
        st.markdown("##### 🎯 Speaker Picks")

        if curated_speakers:
            for item in curated_speakers[:8]:
                detail = parse_detail(item.get("detail_json"))
                score = item.get("relevance_score") or 0
                sc = score_color(score)
                org = detail.get("organization", "")
                why = detail.get("why_trending", "") or detail.get("why_new", "")

                st.markdown(f"""
                <div class="news-item">
                    <div class="news-title">{item['title']}</div>
                    <div class="news-meta">
                        {f"{org} · " if org else ""}Score: <span style="color:{sc};font-weight:600;">{score:.0%}</span>
                    </div>
                    {"<div class='news-summary'>💡 " + why + "</div>" if why else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("아직 연사 후보가 없습니다.")

    # 피드백 히스토리
    st.markdown("""
    <div class="section-header" style="margin-top:2rem;">
        <h2>💬 Team Feedback</h2>
    </div>
    """, unsafe_allow_html=True)

    if isinstance(feedback_list, list) and feedback_list:
        for fb in feedback_list[:10]:
            fb_type_colors = {
                "speaker": "#667eea", "trend": "#00d2ff",
                "direction": "#ffa657", "track": "#00e676",
                "general": "#8b949e",
            }
            fb_color = fb_type_colors.get(fb.get("feedback_type", ""), "#8b949e")

            st.markdown(f"""
            <div class="news-item" style="border-left:3px solid {fb_color};">
                <div style="display:flex;justify-content:space-between;">
                    <span class="tag" style="background:{fb_color}22;color:{fb_color};">{fb.get('feedback_type', '').upper()}</span>
                    <span class="news-meta">{fb.get('created_at', '')[:16]}</span>
                </div>
                <div class="news-summary" style="margin-top:6px;">{fb.get('content', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("피드백이 없습니다. 사이드바에서 피드백을 입력하세요.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5: AGENT ACTIVITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_activity:

    st.markdown("""
    <div class="section-header">
        <h2>🤖 Agent Research Sessions</h2>
    </div>
    """, unsafe_allow_html=True)

    if isinstance(sessions, list) and sessions:
        for sess in sessions[:20]:
            status_icon = {
                "running": "🔄", "completed": "✅", "failed": "❌",
            }.get(sess.get("status"), "❓")
            type_colors = {
                "trend": "#00d2ff", "speaker": "#667eea",
                "daily_scan": "#e94560", "feedback": "#ffa657",
            }
            type_label = {
                "trend": "TREND RESEARCH", "speaker": "SPEAKER SEARCH",
                "daily_scan": "DEEP SCAN", "feedback": "FEEDBACK ANALYSIS",
            }.get(sess.get("session_type"), sess.get("session_type", "").upper())
            tc = type_colors.get(sess.get("session_type"), "#8b949e")

            is_running = sess.get("status") == "running"

            st.markdown(f"""
            <div class="intel-card" style="border-left:3px solid {tc};{'animation:livepulse 2s infinite;' if is_running else ''}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span class="tag" style="background:{tc}22;color:{tc};">{type_label}</span>
                        <span style="font-weight:600;color:#e6edf3;margin-left:6px;">
                            {status_icon} {sess.get('input_query', 'Auto scan')[:80]}
                        </span>
                    </div>
                    <span class="news-meta">{sess.get('created_at', '')[:16]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if sess.get("status") == "completed" and sess.get("result_summary"):
                with st.expander(f"View Results (#{sess['id']})"):
                    st.text(sess["result_summary"][:1000])

                    discussions = api_get(f"/research/sessions/{sess['id']}/discussions")
                    if discussions:
                        st.markdown("**Agent Discussion:**")
                        for disc in discussions:
                            icon = {
                                "proposal": "💡", "critique": "🔍",
                                "revision": "📝", "consensus": "🤝",
                            }.get(disc.get("message_type"), "💭")
                            st.markdown(f"**{icon} {disc['agent_name']}** ({disc['message_type']})")
                            st.text(disc["content"][:500])
    else:
        st.markdown("""
        <div class="intel-card" style="text-align:center;padding:2rem;">
            <div style="font-size:1.5rem;margin-bottom:0.5rem;">🤖</div>
            <div style="color:#8b949e;">No agent activity yet. Start a Deep Research Scan.</div>
        </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하단: 트랙 구성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.expander("📋 Track Configuration"):
    track_list = api_get("/tracks")

    col_add, _ = st.columns([1, 3])
    with col_add:
        with st.popover("➕ Add Track"):
            tn = st.text_input("Name", key="tn_add")
            td = st.text_area("Description", key="td_add", height=60)
            ta = st.text_input("Target Audience", key="ta_add")
            if st.button("Create", key="add_trk"):
                if tn:
                    api_post("/tracks", {"name": tn, "description": td or None, "target_audience": ta or None})
                    st.rerun()

    if isinstance(track_list, list) and track_list:
        cols = st.columns(min(len(track_list), 4))
        for i, track in enumerate(track_list):
            with cols[i % 4]:
                st.markdown(f"""
                <div class="intel-card">
                    <div style="font-weight:700;color:#e6edf3;">{track['name']}</div>
                    <div style="color:#8b949e;font-size:0.8rem;margin-top:4px;">{track.get('description', '')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("No tracks configured yet.")
