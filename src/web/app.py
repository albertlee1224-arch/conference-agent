"""AI SUMMIT 2026 — Live Intelligence Dashboard.

실시간 AI 트렌드/연사 인텔리전스 대시보드.
뉴스 피드처럼 에이전트가 발굴한 최신 정보가 흘러나오는 구조.
"""

import json
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st

# === 설정 ===

import os

def _get_api_base() -> str:
    """환경변수 또는 Streamlit secrets에서 API URL 가져오기."""
    if os.environ.get("API_BASE_URL"):
        return os.environ["API_BASE_URL"]
    try:
        return st.secrets["API_BASE_URL"]
    except (KeyError, FileNotFoundError):
        return "http://localhost:8000/api"

API_BASE = _get_api_base()
REFRESH_INTERVAL = 60  # 자동 새로고침 간격 (초)

st.set_page_config(
    page_title="AI SUMMIT 2026 Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 자동 새로고침
st_autorefresh = st.empty()


# === 커스텀 CSS — 뉴스/주식 대시보드 스타일 ===

st.markdown("""
<style>
/* 전체 폰트/배경 톤 조정 */
.stApp { background-color: #0e1117; }

/* 헤더 영역 */
.hero-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border: 1px solid #1e3a5f;
}
.hero-header h1 {
    color: #e94560;
    font-size: 1.8rem;
    margin: 0;
    font-weight: 800;
}
.hero-header p {
    color: #a0aec0;
    font-size: 0.9rem;
    margin: 0.3rem 0 0 0;
}

/* 라이브 배지 */
.live-badge {
    display: inline-block;
    background: #e94560;
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
    animation: pulse 2s infinite;
    vertical-align: middle;
    margin-left: 8px;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* 피드 카드 */
.feed-card {
    background: #1a1a2e;
    border: 1px solid #2d2d44;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.feed-card:hover {
    border-color: #e94560;
}
.feed-card .card-type {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}
.feed-card .card-type.trend { color: #00d2ff; }
.feed-card .card-type.speaker { color: #ff6b6b; }

/* 스코어 바 */
.score-bar {
    height: 6px;
    background: #2d2d44;
    border-radius: 3px;
    overflow: hidden;
    margin: 4px 0;
}
.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s;
}

/* 사이드바 스타일 */
.sidebar-stat {
    text-align: center;
    padding: 0.8rem;
    background: #1a1a2e;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    border: 1px solid #2d2d44;
}
.sidebar-stat .number {
    font-size: 1.8rem;
    font-weight: 800;
    color: #e94560;
}
.sidebar-stat .label {
    font-size: 0.75rem;
    color: #a0aec0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)


# === API 헬퍼 ===


def api_get(path: str, params: dict | None = None) -> dict | list:
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params, timeout=10)
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
        st.error(f"API 오류: {e}")
        return {}


def api_patch(path: str, data: dict) -> dict:
    try:
        r = httpx.patch(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        st.error(f"API 오류: {e}")
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
        return "#ffab00"
    elif score >= 0.4:
        return "#ff9100"
    return "#ff5252"


# === 데이터 로딩 ===

# 모든 데이터를 한번에 로딩 (라이브 피드용)
suggestions = api_get("/suggestions", {"limit": 100})
trends = api_get("/trends")
speakers = api_get("/speakers", {"limit": 100, "sort": "overall_score"})
stats = api_get("/suggestions/stats")
sessions = api_get("/research/sessions")

pending_suggestions = [s for s in suggestions if s.get("status") == "pending_review"] if isinstance(suggestions, list) else []
trend_suggestions = [s for s in pending_suggestions if s["suggestion_type"] == "trend"]
speaker_suggestions = [s for s in pending_suggestions if s["suggestion_type"] == "speaker"]


# ═══════════════════════════════════════════
# 사이드바 — 컨트롤 센터
# ═══════════════════════════════════════════

with st.sidebar:
    # 시스템 상태
    health = api_get("/health")
    if isinstance(health, dict) and health.get("status") == "ok":
        st.markdown('<div class="sidebar-stat"><div class="number" style="color:#00e676;">ONLINE</div><div class="label">System Status</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sidebar-stat"><div class="number" style="color:#ff5252;">OFFLINE</div><div class="label">System Status</div></div>', unsafe_allow_html=True)

    # 핵심 지표
    if isinstance(stats, dict):
        st.markdown(f'<div class="sidebar-stat"><div class="number">{stats.get("pending", 0)}</div><div class="label">Pending Review</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sidebar-stat"><div class="number">{len(trends) if isinstance(trends, list) else 0}</div><div class="label">Trends Tracked</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-stat"><div class="number">{len(speakers) if isinstance(speakers, list) else 0}</div><div class="label">Speaker Candidates</div></div>', unsafe_allow_html=True)

    # 실행 중인 세션
    running = [s for s in sessions if s.get("status") == "running"] if isinstance(sessions, list) else []
    if running:
        st.markdown(f'<div class="sidebar-stat"><div class="number" style="color:#00d2ff;">{len(running)}</div><div class="label">Active Agents</div></div>', unsafe_allow_html=True)

    st.divider()

    # 액션 버튼
    st.markdown("### Actions")

    if st.button("🔍 AI 스캔 실행", use_container_width=True, type="primary"):
        result = api_post("/suggestions/scan", {})
        if result.get("session_id"):
            st.success(f"스캔 시작 (#{result['session_id']})")
            st.rerun()

    st.divider()

    # 수동 리서치 (축소형)
    with st.expander("📝 수동 리서치"):
        manual_type = st.radio("유형", ["트렌드", "연사"], horizontal=True, key="manual_type")

        if manual_type == "트렌드":
            q = st.text_input("키워드", placeholder="AI Agent, Multimodal AI", key="mq")
            if st.button("실행", key="run_manual_t", use_container_width=True):
                if q:
                    r = api_post("/research/trends", {"query": q})
                    if r.get("session_id"):
                        st.success(f"시작 (#{r['session_id']})")
        else:
            topic = st.text_input("주제", placeholder="AI Agent", key="ms_topic")
            tier = st.selectbox("티어", ["tier3_track", "tier1_keynote"], key="ms_tier")
            prefs = st.text_input("선호 조건", key="ms_prefs")
            if st.button("실행", key="run_manual_s", use_container_width=True):
                if topic:
                    r = api_post("/research/speakers", {
                        "topic": topic, "tier": tier,
                        "preferences": prefs or None,
                    })
                    if r.get("session_id"):
                        st.success(f"시작 (#{r['session_id']})")

    with st.expander("💬 피드백 입력"):
        fb = st.text_area("내용", height=80, key="fb_in", placeholder="Healthcare AI 연사 추가 필요")
        fb_type = st.selectbox("유형", ["general", "direction", "speaker", "trend", "track"], key="fb_t")
        if st.button("제출", key="fb_submit", use_container_width=True):
            if fb:
                r = api_post("/feedback", {"content": fb, "feedback_type": fb_type})
                if r.get("id"):
                    st.success("피드백 제출 완료")

    st.divider()
    st.caption("AI SUMMIT AND EXPO 2026")
    st.caption("Conference Intelligence v0.2.0")
    st.markdown("[API Docs](http://localhost:8000/docs)")


# ═══════════════════════════════════════════
# 메인 영역 — 라이브 인텔리전스 피드
# ═══════════════════════════════════════════

# 헤더
st.markdown("""
<div class="hero-header">
    <h1>AI SUMMIT 2026 <span class="live-badge">LIVE</span></h1>
    <p>Conference Intelligence Dashboard — 에이전트가 실시간으로 발굴하는 AI 트렌드와 연사 후보</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
# 섹션 1: 검토 대기 — 에이전트가 찾은 새로운 발견
# ═══════════════════════════════════════════

if pending_suggestions:
    st.markdown(f"## 🔔 검토 대기 ({len(pending_suggestions)}건)")
    st.caption("에이전트가 자동 발굴한 최신 트렌드와 연사입니다. 승인하면 정식 등록됩니다.")

    for s in pending_suggestions:
        detail = {}
        if s.get("detail_json"):
            try:
                detail = json.loads(s["detail_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        is_trend = s["suggestion_type"] == "trend"
        type_label = "TREND" if is_trend else "SPEAKER"
        type_class = "trend" if is_trend else "speaker"
        score = s.get("relevance_score") or 0
        sc = score_color(score)

        col_main, col_act = st.columns([5, 1])

        with col_main:
            # 타입 배지
            st.markdown(f'<div class="feed-card"><div class="card-type {type_class}">{type_label}</div>', unsafe_allow_html=True)

            if is_trend:
                st.markdown(f"**{s['title']}**")
                if s.get("summary"):
                    st.write(s["summary"])
                cat = detail.get("category", "")
                if cat:
                    st.caption(f"카테고리: {cat}")
            else:
                org = detail.get("organization", "")
                title_str = detail.get("title", "")
                tier = detail.get("suggested_tier", "")
                tier_icon = {"tier1_keynote": "🏆 Keynote", "tier3_track": "📌 Track"}.get(tier, "")

                header = f"**{s['title']}**"
                if title_str or org:
                    header += f" — {title_str} @ {org}"
                st.markdown(header)
                if tier_icon:
                    st.caption(tier_icon)
                if s.get("summary"):
                    st.write(s["summary"])
                if detail.get("linkedin_url"):
                    st.markdown(f"[LinkedIn Profile]({detail['linkedin_url']})")

            # 적합도 바
            st.markdown(
                f'<div class="score-bar"><div class="score-bar-fill" '
                f'style="width:{score*100:.0f}%;background:{sc};"></div></div>'
                f'<span style="color:{sc};font-size:0.85rem;font-weight:700;">'
                f'{score:.0%} 적합도</span>',
                unsafe_allow_html=True,
            )

            # 근거 링크
            if s.get("source_urls"):
                try:
                    urls = json.loads(s["source_urls"]) if isinstance(s["source_urls"], str) else s["source_urls"]
                    if urls:
                        with st.expander("Sources"):
                            for u in urls[:5]:
                                st.markdown(f"- {u}")
                except (json.JSONDecodeError, TypeError):
                    pass

            st.markdown('</div>', unsafe_allow_html=True)

        with col_act:
            st.write("")
            st.write("")
            if st.button("✅ 승인", key=f"ap_{s['id']}", use_container_width=True, type="primary"):
                api_patch(f"/suggestions/{s['id']}/approve", {"status": "approved"})
                st.rerun()
            if st.button("❌ 패스", key=f"dm_{s['id']}", use_container_width=True):
                api_patch(f"/suggestions/{s['id']}/dismiss", {"status": "dismissed"})
                st.rerun()

    st.divider()


# ═══════════════════════════════════════════
# 섹션 2: 트렌드 인텔리전스 (확정된 트렌드)
# ═══════════════════════════════════════════

st.markdown("## 📊 Trend Intelligence")

if isinstance(trends, list) and trends:
    # 상위 트렌드 메트릭
    sorted_trends = sorted(trends, key=lambda t: t.get("relevance_score") or 0, reverse=True)
    top_n = min(5, len(sorted_trends))
    cols = st.columns(top_n)
    for i, t in enumerate(sorted_trends[:top_n]):
        with cols[i]:
            score = t.get("relevance_score") or 0
            auto = " 🤖" if t.get("is_auto_discovered") else ""
            st.metric(
                label=f"{t['keyword']}{auto}",
                value=f"{score:.0%}",
                delta=t.get("category", ""),
            )

    # 전체 트렌드 테이블
    with st.expander(f"전체 트렌드 ({len(trends)}건)", expanded=False):
        df = pd.DataFrame(trends)
        display_cols = ["keyword", "category", "description", "relevance_score"]
        available = [c for c in display_cols if c in df.columns]
        if available:
            st.dataframe(
                df[available].sort_values("relevance_score", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "keyword": st.column_config.TextColumn("Keyword", width="medium"),
                    "category": st.column_config.TextColumn("Category", width="medium"),
                    "description": st.column_config.TextColumn("Description", width="large"),
                    "relevance_score": st.column_config.ProgressColumn(
                        "Score", min_value=0, max_value=1, format="%.0%%"
                    ),
                },
            )

        # 카테고리 분포
        if "category" in df.columns:
            cat_counts = df["category"].value_counts()
            if not cat_counts.empty:
                st.bar_chart(cat_counts, height=200)

        # 근거 자료
        for _, row in df.iterrows():
            evidence = row.get("evidence")
            if evidence:
                try:
                    ev_list = json.loads(evidence) if isinstance(evidence, str) else evidence
                    if ev_list:
                        auto_badge = " 🤖" if row.get("is_auto_discovered") else ""
                        with st.expander(f"{row.get('keyword', '')}{auto_badge}"):
                            st.write(row.get("description", ""))
                            for ev in ev_list:
                                src = ev.get("source", "")
                                url = ev.get("url", "")
                                snippet = ev.get("snippet", "")
                                if url:
                                    st.markdown(f"- [{src}]({url}): {snippet}")
                                else:
                                    st.markdown(f"- {src}: {snippet}")
                except (json.JSONDecodeError, TypeError):
                    pass
else:
    st.info("트렌드 데이터 없음 — 사이드바에서 AI 스캔을 실행하세요")

st.divider()


# ═══════════════════════════════════════════
# 섹션 3: 연사 인텔리전스 (확정된 연사)
# ═══════════════════════════════════════════

st.markdown("## 🎤 Speaker Intelligence")

if isinstance(speakers, list) and speakers:
    # 필터바
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        f_tier = st.selectbox("Tier", ["All", "tier1_keynote", "tier3_track", "unassigned"], key="ft")
    with col_f2:
        f_status = st.selectbox("Status", ["All", "candidate", "shortlisted", "contacting", "confirmed"], key="fs")
    with col_f3:
        f_search = st.text_input("Search", placeholder="이름, 소속, 키워드...", key="fsearch")

    # 필터 적용
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

    st.caption(f"{len(filtered)}명 표시")

    # 연사 카드 그리드
    for sp in filtered:
        col_info, col_score, col_ctrl = st.columns([3, 2, 1])

        with col_info:
            tier_icons = {"tier1_keynote": "🏆", "tier3_track": "📌"}
            tier_icon = tier_icons.get(sp.get("tier"), "⬜")
            auto = " 🤖" if sp.get("is_auto_discovered") else ""
            status_colors = {
                "confirmed": "🟢", "shortlisted": "🟡",
                "contacting": "🔵", "candidate": "⚪",
                "declined": "🔴", "rejected": "🔴",
            }
            status_dot = status_colors.get(sp.get("status"), "⚪")

            st.markdown(
                f"### {tier_icon} {sp['name']}{auto}\n"
                f"{status_dot} {sp.get('status', 'candidate')} | "
                f"**{sp.get('title', '')}** @ {sp.get('organization', 'N/A')} | "
                f"{sp.get('country', '')}"
            )
            if sp.get("recommendation_reason"):
                st.caption(sp["recommendation_reason"][:150])
            links = []
            if sp.get("linkedin_url"):
                links.append(f"[LinkedIn]({sp['linkedin_url']})")
            if sp.get("website_url"):
                links.append(f"[Website]({sp['website_url']})")
            if links:
                st.markdown(" | ".join(links))

        with col_score:
            overall = sp.get("overall_score") or 0
            sc = score_color(overall)
            st.markdown(
                f'<div style="text-align:center;">'
                f'<span style="font-size:2rem;font-weight:800;color:{sc};">'
                f'{overall:.0%}</span><br>'
                f'<span style="color:#a0aec0;font-size:0.75rem;">OVERALL SCORE</span></div>',
                unsafe_allow_html=True,
            )
            score_items = {
                "EXP": sp.get("expertise_score") or 0,
                "NAME": sp.get("name_value_score") or 0,
                "TALK": sp.get("speaking_score") or 0,
                "FIT": sp.get("relevance_score") or 0,
            }
            for label, val in score_items.items():
                c = score_color(val)
                st.markdown(
                    f'<span style="color:#a0aec0;font-size:0.7rem;">{label}</span> '
                    f'<div class="score-bar"><div class="score-bar-fill" '
                    f'style="width:{val*100:.0f}%;background:{c};"></div></div>',
                    unsafe_allow_html=True,
                )

        with col_ctrl:
            new_st = st.selectbox(
                "상태",
                ["candidate", "shortlisted", "contacting",
                 "confirmed", "declined", "rejected"],
                index=["candidate", "shortlisted", "contacting",
                       "confirmed", "declined", "rejected"].index(
                    sp.get("status", "candidate")
                ),
                key=f"st_{sp['id']}",
                label_visibility="collapsed",
            )
            if new_st != sp.get("status"):
                api_patch(f"/speakers/{sp['id']}", {"status": new_st})
                st.rerun()

        st.divider()
else:
    st.info("연사 데이터 없음 — 사이드바에서 AI 스캔을 실행하세요")


# ═══════════════════════════════════════════
# 섹션 4: 에이전트 활동 로그
# ═══════════════════════════════════════════

with st.expander("🤖 Agent Activity Log"):
    if isinstance(sessions, list) and sessions:
        for sess in sessions[:15]:
            status_icon = {
                "running": "🔄", "completed": "✅", "failed": "❌",
            }.get(sess.get("status"), "❓")
            type_label = {
                "trend": "TREND", "speaker": "SPEAKER",
                "daily_scan": "AUTO SCAN", "feedback": "FEEDBACK",
            }.get(sess.get("session_type"), sess.get("session_type", ""))

            st.markdown(
                f"{status_icon} **[{type_label}]** {sess.get('input_query', '')[:80]} "
                f"— {sess.get('created_at', '')[:16]}"
            )

            if sess.get("status") == "completed" and sess.get("result_summary"):
                with st.expander(f"결과 (#{sess['id']})"):
                    st.text(sess["result_summary"][:500])

                    discussions = api_get(f"/research/sessions/{sess['id']}/discussions")
                    if discussions:
                        st.markdown("**에이전트 토론:**")
                        for disc in discussions:
                            icon = {
                                "proposal": "💡", "critique": "🔍",
                                "revision": "📝", "consensus": "🤝",
                            }.get(disc.get("message_type"), "💭")
                            st.markdown(
                                f"{icon} **{disc['agent_name']}** "
                                f"({disc['message_type']})"
                            )
                            st.text(disc["content"][:300])
    else:
        st.caption("아직 에이전트 활동이 없습니다.")


# ═══════════════════════════════════════════
# 하단: 트랙 구성 (접혀있는 상태)
# ═══════════════════════════════════════════

with st.expander("📋 Track Configuration"):
    track_list = api_get("/tracks")

    col_add, _ = st.columns([1, 3])
    with col_add:
        with st.popover("➕ 트랙 추가"):
            tn = st.text_input("이름", key="tn_add")
            td = st.text_area("설명", key="td_add", height=60)
            ta = st.text_input("대상", key="ta_add")
            if st.button("추가", key="add_trk"):
                if tn:
                    api_post("/tracks", {"name": tn, "description": td or None, "target_audience": ta or None})
                    st.rerun()

    if isinstance(track_list, list) and track_list:
        cols = st.columns(min(len(track_list), 4))
        for i, track in enumerate(track_list):
            with cols[i % 4]:
                st.markdown(f"**{track['name']}**")
                if track.get("description"):
                    st.caption(track["description"])

                t_trends = track.get("trends", [])
                if t_trends:
                    for t in t_trends:
                        st.markdown(f"- 📊 {t.get('keyword', '')}")

                t_speakers = api_get("/speakers", {"track_id": track["id"]})
                if t_speakers:
                    for sp in t_speakers[:3]:
                        st.markdown(f"- 🎤 {sp['name']}")
    else:
        st.caption("트랙을 추가하세요.")
