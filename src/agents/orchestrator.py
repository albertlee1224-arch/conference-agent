"""Orchestrator — Anthropic SDK 기반 팀에이전트 오케스트레이션.

claude-agent-sdk 없이 직접 Anthropic API를 호출하여
트렌드/연사 리서치, 일일 스캔, 피드백 처리를 수행합니다.
멀티에이전트는 순차 호출 패턴으로 구현합니다.
"""

from __future__ import annotations

import logging
from typing import Any

import aiosqlite

from src.agents.agent_loop import WEB_SEARCH_TOOL, run_agent
from src.agents.tool_defs import (
    DAILY_SCAN_TOOLS,
    FEEDBACK_TOOLS,
    PERSONA_TOOLS,
    SPEAKER_RESEARCH_TOOLS,
    TOOL_HANDLERS,
    TREND_RESEARCH_TOOLS,
)
from src.agents.personas import PERSONA_AGENTS
from src.config import settings
from src.db import queries as q
from src.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


# ── 페르소나 평가 공통 함수 ─────────────────────────────────


async def _run_persona_evaluation(
    research_result: str,
    session_id: int,
    context_label: str,
) -> str:
    """4명의 페르소나 에이전트에게 리서치 결과를 순차 평가받는다."""
    evaluations: list[str] = []

    for persona_name, persona_config in PERSONA_AGENTS.items():
        tools = list(PERSONA_TOOLS)
        if persona_config.get("tools"):
            tools.append(WEB_SEARCH_TOOL)

        prompt = (
            f"리서치 세션 ID: {session_id}\n\n"
            f"당신은 {persona_config['description']}입니다.\n\n"
            f"다음 {context_label} 결과를 당신의 관점에서 평가하세요:\n\n"
            f"{research_result}\n\n"
            f"평가 후 save_discussion 도구로 평가 내용을 저장하세요.\n"
            f"agent_name: '{persona_name}', message_type: 'critique'"
        )

        logger.info(f"페르소나 평가 시작: {persona_name}")
        evaluation = await run_agent(
            system_prompt=persona_config["prompt"],
            user_prompt=prompt,
            tools=tools,
            tool_handlers=TOOL_HANDLERS,
            max_turns=5,
        )
        evaluations.append(f"[{persona_name}]\n{evaluation}")

    return "\n\n---\n\n".join(evaluations)


# ── 메인 실행 함수 ──────────────────────────────────────────


async def run_trend_research(query_text: str, session_id: int) -> str:
    """트렌드 리서치 + 페르소나 토론 실행."""
    from src.prompts.trend_research import TREND_RESEARCH_PROMPT

    logger.info(f"트렌드 리서치 시작 (session={session_id}, query={query_text})")

    # 1단계: 트렌드 리서치
    research_prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"다음 주제에 대해 AI SUMMIT AND EXPO 2026에 적합한 트렌드를 리서치하세요: "
        f"{query_text}\n\n"
        f"발견한 각 트렌드를 save_trend 도구로 DB에 저장하세요."
    )

    research_result = await run_agent(
        system_prompt=TREND_RESEARCH_PROMPT,
        user_prompt=research_prompt,
        tools=TREND_RESEARCH_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=settings.max_agent_turns,
    )
    logger.info("트렌드 리서치 1단계(리서치) 완료")

    # 2단계: 페르소나 평가
    persona_feedback = await _run_persona_evaluation(
        research_result, session_id, "트렌드 리서치"
    )
    logger.info("트렌드 리서치 2단계(페르소나 평가) 완료")

    # 3단계: 피드백 반영 및 최종 확정
    final_prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"## 1차 리서치 결과\n{research_result}\n\n"
        f"## 페르소나 패널 피드백\n{persona_feedback}\n\n"
        f"페르소나 피드백을 반영하여 트렌드 리스트를 최종 확정하세요.\n"
        f"필요한 경우 점수를 조정하거나 새 트렌드를 추가하세요.\n"
        f"최종 결론을 save_discussion(message_type='consensus')로 저장하세요."
    )

    final_result = await run_agent(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        user_prompt=final_prompt,
        tools=TREND_RESEARCH_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=10,
    )

    logger.info(f"트렌드 리서치 완료 (session={session_id})")
    return final_result


async def run_speaker_research(
    topic: str,
    tier: str = "tier3_track",
    count: int = 10,
    preferences: str | None = None,
    session_id: int = 0,
) -> str:
    """연사 추천 + 페르소나 토론 실행."""
    from src.prompts.speaker_research import SPEAKER_RESEARCH_PROMPT

    logger.info(f"연사 추천 시작 (session={session_id}, topic={topic})")

    # 1단계: 연사 리서치
    research_prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"주제: {topic}\n"
        f"티어: {tier}\n"
        f"추천 수: {count}명\n"
    )
    if preferences:
        research_prompt += f"선호 조건: {preferences}\n"
    research_prompt += (
        f"\n해외 연사 후보를 발굴하고, 각 후보를 save_speaker 도구로 DB에 저장하세요."
    )

    research_result = await run_agent(
        system_prompt=SPEAKER_RESEARCH_PROMPT,
        user_prompt=research_prompt,
        tools=SPEAKER_RESEARCH_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=settings.max_agent_turns,
    )
    logger.info("연사 추천 1단계(리서치) 완료")

    # 2단계: 페르소나 평가
    persona_feedback = await _run_persona_evaluation(
        research_result, session_id, "연사 추천"
    )
    logger.info("연사 추천 2단계(페르소나 평가) 완료")

    # 3단계: 피드백 반영 및 최종 확정
    final_prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"## 1차 연사 후보\n{research_result}\n\n"
        f"## 페르소나 패널 피드백\n{persona_feedback}\n\n"
        f"패널 합의를 바탕으로 연사 스코어를 조정하고 최종 확정하세요.\n"
        f"필요하면 score_speaker 도구로 점수를 재계산하세요.\n"
        f"최종 결론을 save_discussion(message_type='consensus')로 저장하세요."
    )

    final_result = await run_agent(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        user_prompt=final_prompt,
        tools=SPEAKER_RESEARCH_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=10,
    )

    logger.info(f"연사 추천 완료 (session={session_id})")
    return final_result


async def run_daily_scan(session_id: int) -> str:
    """매일 자동 실행되는 트렌드/연사 통합 스캔."""
    from src.prompts.daily_scan import (
        DAILY_SCAN_ORCHESTRATOR_PROMPT,
        DAILY_SPEAKER_SCAN_PROMPT,
        DAILY_TREND_SCAN_PROMPT,
    )

    logger.info(f"일일 스캔 시작 (session={session_id})")

    # 기존 트렌드/연사 목록 — 중복 방지용 컨텍스트
    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    try:
        trends = await q.list_trends(db)
        speakers = await q.list_speakers(db)
    finally:
        await db.close()

    trends_text = "\n".join(
        f"- {t['keyword']} ({t.get('category', '')})" for t in trends
    ) if trends else "아직 없음"

    speakers_text = "\n".join(
        f"- {s['name']} ({s.get('organization', '')})" for s in speakers
    ) if speakers else "아직 없음"

    # .replace()로 치환 — 프롬프트 내 JSON 중괄호와 충돌 방지
    trend_prompt = DAILY_TREND_SCAN_PROMPT.replace(
        "{existing_trends}", trends_text,
    )
    speaker_prompt = DAILY_SPEAKER_SCAN_PROMPT.replace(
        "{existing_trends}", trends_text,
    ).replace(
        "{existing_speakers}", speakers_text,
    )

    # 1단계: 트렌드 스캔
    trend_scan_prompt = (
        f"일일 스캔 세션 ID: {session_id}\n\n"
        f"최신 AI 트렌드를 탐색하고 save_daily_suggestion으로 저장하세요."
    )

    trend_result = await run_agent(
        system_prompt=trend_prompt,
        user_prompt=trend_scan_prompt,
        tools=DAILY_SCAN_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=settings.max_agent_turns,
    )
    logger.info("일일 스캔 — 트렌드 스캔 완료")

    # 2단계: 연사 스캔
    speaker_scan_prompt = (
        f"일일 스캔 세션 ID: {session_id}\n\n"
        f"새 해외 연사 후보를 탐색하고 save_daily_suggestion으로 저장하세요."
    )

    speaker_result = await run_agent(
        system_prompt=speaker_prompt,
        user_prompt=speaker_scan_prompt,
        tools=DAILY_SCAN_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=settings.max_agent_turns,
    )
    logger.info("일일 스캔 — 연사 스캔 완료")

    # 3단계: 페르소나 간략 검증
    combined_result = (
        f"## 트렌드 스캔 결과\n{trend_result}\n\n"
        f"## 연사 스캔 결과\n{speaker_result}"
    )

    persona_feedback = await _run_persona_evaluation(
        combined_result, session_id, "일일 스캔"
    )
    logger.info("일일 스캔 — 페르소나 검증 완료")

    # 4단계: 최종 정리
    final_prompt = (
        f"세션 ID: {session_id}\n\n"
        f"## 스캔 결과\n{combined_result}\n\n"
        f"## 페르소나 피드백\n{persona_feedback}\n\n"
        f"오늘의 일일 스캔 결과를 종합하세요.\n"
        f"save_discussion(message_type='consensus')으로 최종 요약을 저장하세요."
    )

    final_result = await run_agent(
        system_prompt=DAILY_SCAN_ORCHESTRATOR_PROMPT,
        user_prompt=final_prompt,
        tools=DAILY_SCAN_TOOLS,
        tool_handlers=TOOL_HANDLERS,
        max_turns=10,
    )

    logger.info(f"일일 스캔 완료 (session={session_id})")
    return final_result


async def run_feedback_processing(
    feedback_content: str,
    feedback_type: str,
    session_id: int,
) -> str:
    """피드백 분석 및 반영."""
    from src.prompts.feedback import FEEDBACK_PROMPT

    logger.info(f"피드백 처리 시작 (session={session_id}, type={feedback_type})")

    prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"피드백 유형: {feedback_type}\n"
        f"피드백 내용: {feedback_content}\n\n"
        f"이 피드백을 분석하고 적절한 조치를 취하세요.\n"
        f"save_discussion 도구로 처리 과정을 기록하세요."
    )

    result = await run_agent(
        system_prompt=FEEDBACK_PROMPT,
        user_prompt=prompt,
        tools=FEEDBACK_TOOLS + [WEB_SEARCH_TOOL],
        tool_handlers=TOOL_HANDLERS,
        max_turns=settings.max_agent_turns,
    )

    logger.info(f"피드백 처리 완료 (session={session_id})")
    return result


async def run_planner_evaluation(session_id: int) -> str:
    """DB 현황 평가 → 부족한 부분 식별 → 자동 리서치 트리거."""
    from src.prompts.planner_director import PLANNER_DIRECTOR_PROMPT

    logger.info(f"Planner 평가 시작 (session={session_id})")

    # DB 통계 수집
    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    try:
        trends = await q.list_trends(db)
        speakers = await q.list_speakers(db)

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM daily_suggestions WHERE status = 'pending_review'"
        )
        pending = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM daily_suggestions WHERE status = 'approved'"
        )
        approved = (await cursor.fetchone())["cnt"]
    finally:
        await db.close()

    # 통계 텍스트 구성
    stats_text = (
        f"## 현재 데이터 현황\n"
        f"- 등록된 트렌드: {len(trends)}개\n"
        f"- 등록된 연사 후보: {len(speakers)}개\n"
        f"- 대기 중인 제안: {pending}개\n"
        f"- 승인된 제안: {approved}개\n\n"
    )

    if trends:
        # 카테고리별 분포
        categories: dict[str, int] = {}
        for t in trends:
            cat = t.get("category", "미분류") or "미분류"
            categories[cat] = categories.get(cat, 0) + 1
        stats_text += "### 트렌드 카테고리 분포\n"
        for cat, cnt in sorted(categories.items(), key=lambda x: -x[1]):
            stats_text += f"- {cat}: {cnt}개\n"

    if speakers:
        # 티어별 분포
        tiers: dict[str, int] = {}
        for s in speakers:
            tier = s.get("tier", "unassigned") or "unassigned"
            tiers[tier] = tiers.get(tier, 0) + 1
        stats_text += "\n### 연사 티어 분포\n"
        for tier, cnt in sorted(tiers.items()):
            stats_text += f"- {tier}: {cnt}명\n"

        # 국가별 분포
        countries: dict[str, int] = {}
        for s in speakers:
            country = s.get("country", "미상") or "미상"
            countries[country] = countries.get(country, 0) + 1
        stats_text += "\n### 연사 국가 분포\n"
        for country, cnt in sorted(countries.items(), key=lambda x: -x[1])[:10]:
            stats_text += f"- {country}: {cnt}명\n"

    prompt = (
        f"Planner 평가 세션 ID: {session_id}\n\n"
        f"{stats_text}\n\n"
        f"위 데이터 현황을 분석하고, 개선 과제를 도출하세요.\n"
        f"각 과제를 JSON 형태로 출력하세요."
    )

    evaluation_result = await run_agent(
        system_prompt=PLANNER_DIRECTOR_PROMPT,
        user_prompt=prompt,
        tools=DAILY_SCAN_TOOLS,
        tool_handlers=TOOL_HANDLERS,
        max_turns=10,
    )

    # 자동 실행이 활성화된 경우, 평가 결과에서 과제를 파싱하여 실행
    if settings.planner_enabled and settings.planner_auto_execute:
        import json

        try:
            # 결과에서 JSON 배열 추출 시도
            tasks = _extract_tasks_from_result(evaluation_result)
            for task in tasks:
                if task.get("priority") == "high":
                    task_type = task.get("type", "")
                    task_query = task.get("query", "")
                    logger.info(
                        f"Planner 자동 실행: {task_type} — {task_query}"
                    )

                    # planner_tasks 테이블에 기록
                    db = await aiosqlite.connect(str(settings.database_path))
                    db.row_factory = aiosqlite.Row
                    try:
                        await db.execute(
                            """INSERT INTO planner_tasks
                               (task_type, priority, query, reason, status, session_id)
                               VALUES (?, ?, ?, ?, 'running', ?)""",
                            (
                                task_type,
                                task["priority"],
                                task_query,
                                task.get("reason", ""),
                                session_id,
                            ),
                        )
                        await db.commit()
                    finally:
                        await db.close()

                    if task_type == "trend":
                        await run_trend_research(task_query, session_id)
                    elif task_type == "speaker":
                        await run_speaker_research(task_query, session_id=session_id)
        except Exception as e:
            logger.warning(f"Planner 자동 실행 중 오류 (비치명적): {e}")

    logger.info(f"Planner 평가 완료 (session={session_id})")
    return evaluation_result


def _extract_tasks_from_result(result: str) -> list[dict[str, Any]]:
    """에이전트 응답에서 JSON 과제 배열을 추출."""
    import json
    import re

    # JSON 배열 패턴 찾기
    match = re.search(r'\[[\s\S]*?\]', result)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return []
