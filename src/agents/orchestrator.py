"""Orchestrator — 팀에이전트 토론 조율 및 에이전트 실행.

Claude Agent SDK의 query() + AgentDefinition을 활용하여
기능 에이전트(리서치)와 페르소나 에이전트(평가)의 토론을 진행합니다.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)

logger = logging.getLogger(__name__)

from src.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from src.agents.trend_researcher import TREND_RESEARCHER_AGENT
from src.agents.speaker_researcher import SPEAKER_RESEARCHER_AGENT
from src.agents.personas import PERSONA_AGENTS
from src.tools.db_tools import (
    save_trend_handler,
    save_speaker_handler,
    get_trends_handler,
    get_speakers_handler,
    update_speaker_status_handler,
    save_discussion_handler,
    save_daily_suggestion_handler,
)
from src.tools.scoring_tools import score_speaker_handler
from src.config import settings


# === 커스텀 도구를 @tool 데코레이터로 래핑 ===


@tool(
    "save_trend",
    "트렌드 키워드를 데이터베이스에 저장합니다",
    {
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "트렌드 키워드 (영문)"},
            "category": {"type": "string", "description": "분류"},
            "description": {"type": "string", "description": "설명 (한국어)"},
            "evidence": {
                "type": "array",
                "description": "근거 자료 [{source, url, snippet}]",
            },
            "source_conferences": {
                "type": "array",
                "description": "출처 컨퍼런스 목록",
            },
            "relevance_score": {
                "type": "number",
                "description": "적합도 0.0~1.0",
            },
            "session_id": {"type": "integer", "description": "리서치 세션 ID"},
        },
        "required": ["keyword", "description"],
    },
)
async def save_trend(args: dict[str, Any]) -> dict[str, Any]:
    return await save_trend_handler(args)


@tool(
    "save_speaker",
    "연사 후보 정보를 데이터베이스에 저장합니다",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "연사 이름 (영문)"},
            "name_ko": {"type": "string"},
            "title": {"type": "string", "description": "직함"},
            "organization": {"type": "string", "description": "소속"},
            "country": {"type": "string"},
            "bio": {"type": "string"},
            "expertise": {"type": "array", "items": {"type": "string"}},
            "tier": {
                "type": "string",
                "enum": ["tier1_keynote", "tier3_track", "unassigned"],
            },
            "overall_score": {"type": "number"},
            "expertise_score": {"type": "number"},
            "name_value_score": {"type": "number"},
            "speaking_score": {"type": "number"},
            "relevance_score": {"type": "number"},
            "linkedin_url": {"type": "string"},
            "website_url": {"type": "string"},
            "speaking_history": {"type": "array"},
            "publications": {"type": "array"},
            "recommendation_reason": {"type": "string"},
            "source_channel": {"type": "string"},
            "session_id": {"type": "integer"},
        },
        "required": ["name", "recommendation_reason"],
    },
)
async def save_speaker(args: dict[str, Any]) -> dict[str, Any]:
    return await save_speaker_handler(args)


@tool(
    "get_trends",
    "저장된 트렌드 목록을 조회합니다",
    {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
        },
    },
)
async def get_trends(args: dict[str, Any]) -> dict[str, Any]:
    return await get_trends_handler(args)


@tool(
    "get_speakers",
    "저장된 연사 후보 목록을 조회합니다",
    {
        "type": "object",
        "properties": {
            "tier": {"type": "string"},
            "status": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
        },
    },
)
async def get_speakers(args: dict[str, Any]) -> dict[str, Any]:
    return await get_speakers_handler(args)


@tool(
    "update_speaker_status",
    "연사 상태를 변경합니다",
    {
        "type": "object",
        "properties": {
            "speaker_id": {"type": "integer"},
            "status": {
                "type": "string",
                "enum": [
                    "candidate", "shortlisted", "contacting",
                    "confirmed", "declined", "rejected",
                ],
            },
        },
        "required": ["speaker_id", "status"],
    },
)
async def update_speaker_status(args: dict[str, Any]) -> dict[str, Any]:
    return await update_speaker_status_handler(args)


@tool(
    "score_speaker",
    "연사 적합성 종합 점수를 계산합니다",
    {
        "type": "object",
        "properties": {
            "expertise_score": {"type": "number"},
            "name_value_score": {"type": "number"},
            "speaking_score": {"type": "number"},
            "relevance_score": {"type": "number"},
        },
        "required": [
            "expertise_score",
            "name_value_score",
            "speaking_score",
            "relevance_score",
        ],
    },
)
async def score_speaker(args: dict[str, Any]) -> dict[str, Any]:
    return await score_speaker_handler(args)


@tool(
    "save_discussion",
    "에이전트 토론 기록을 저장합니다",
    {
        "type": "object",
        "properties": {
            "session_id": {"type": "integer"},
            "agent_name": {"type": "string"},
            "message_type": {
                "type": "string",
                "enum": ["proposal", "critique", "revision", "consensus"],
            },
            "content": {"type": "string"},
            "round_number": {"type": "integer", "default": 1},
        },
        "required": ["session_id", "agent_name", "message_type", "content"],
    },
)
async def save_discussion(args: dict[str, Any]) -> dict[str, Any]:
    return await save_discussion_handler(args)


@tool(
    "save_daily_suggestion",
    "일일 자동 스캔에서 발굴한 트렌드/연사 제안을 저장합니다",
    {
        "type": "object",
        "properties": {
            "suggestion_type": {
                "type": "string",
                "enum": ["trend", "speaker"],
                "description": "제안 유형",
            },
            "title": {"type": "string", "description": "트렌드 키워드 또는 연사 이름 (영문)"},
            "summary": {"type": "string", "description": "왜 새롭고 중요한지 설명 (한국어)"},
            "detail_json": {"type": "string", "description": "상세 정보 JSON 문자열"},
            "source_urls": {"type": "string", "description": "근거 URL JSON 배열"},
            "relevance_score": {"type": "number", "description": "적합도 0.0~1.0"},
            "session_id": {"type": "integer", "description": "스캔 세션 ID"},
        },
        "required": ["suggestion_type", "title", "summary"],
    },
)
async def save_daily_suggestion(args: dict[str, Any]) -> dict[str, Any]:
    return await save_daily_suggestion_handler(args)


# === MCP 서버 구성 ===


conference_tools_server = create_sdk_mcp_server(
    name="conference_tools",
    version="1.0.0",
    tools=[
        save_trend,
        save_speaker,
        get_trends,
        get_speakers,
        update_speaker_status,
        score_speaker,
        save_discussion,
        save_daily_suggestion,
    ],
)


# === 에이전트 정의 빌드 ===


def _build_agents(
    daily_scan_context: dict[str, str] | None = None,
) -> dict[str, AgentDefinition]:
    """기능 에이전트 + 페르소나 에이전트를 AgentDefinition으로 변환."""
    from src.prompts.daily_scan import (
        DAILY_TREND_SCAN_PROMPT,
        DAILY_SPEAKER_SCAN_PROMPT,
    )

    agents = {}

    # 기능 에이전트
    for name, config in [
        ("trend-researcher", TREND_RESEARCHER_AGENT),
        ("speaker-researcher", SPEAKER_RESEARCHER_AGENT),
    ]:
        agents[name] = AgentDefinition(
            description=config["description"],
            prompt=config["prompt"],
            tools=config["tools"],
            model=config.get("model"),
        )

    # 일일 스캔 에이전트 (컨텍스트가 있을 때만 추가)
    if daily_scan_context:
        agents["trend-scanner"] = AgentDefinition(
            description="최신 AI 트렌드를 능동적으로 탐지하는 에이전트",
            prompt=DAILY_TREND_SCAN_PROMPT.format(
                existing_trends=daily_scan_context.get("trends", "없음"),
            ),
            tools=[
                "WebSearch",
                "WebFetch",
                "mcp__conference_tools__save_daily_suggestion",
            ],
            model="sonnet",
        )
        agents["speaker-scanner"] = AgentDefinition(
            description="새로운 해외 연사 후보를 능동적으로 발굴하는 에이전트",
            prompt=DAILY_SPEAKER_SCAN_PROMPT.format(
                existing_trends=daily_scan_context.get("trends", "없음"),
                existing_speakers=daily_scan_context.get("speakers", "없음"),
            ),
            tools=[
                "WebSearch",
                "WebFetch",
                "mcp__conference_tools__save_daily_suggestion",
            ],
            model="sonnet",
        )

    # 페르소나 에이전트
    for name, config in PERSONA_AGENTS.items():
        agents[name] = AgentDefinition(
            description=config["description"],
            prompt=config["prompt"],
            tools=config["tools"],
            model=config.get("model"),
        )

    return agents


# === 메인 실행 함수 ===


async def _collect_results(messages_iter) -> str:
    """에이전트 메시지 스트림에서 텍스트 결과를 수집."""
    result_parts: list[str] = []
    async for message in messages_iter:
        if hasattr(message, "content") and message.content:
            for block in message.content:
                if hasattr(block, "text"):
                    result_parts.append(block.text)
    return "\n".join(result_parts) if result_parts else ""


async def run_trend_research(query_text: str, session_id: int) -> str:
    """트렌드 리서치 + 페르소나 토론 실행."""
    logger.info(f"트렌드 리서치 시작 (session={session_id}, query={query_text})")

    prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"다음 주제에 대해 AI SUMMIT AND EXPO 2026에 적합한 트렌드를 리서치하세요: "
        f"{query_text}\n\n"
        f"트렌드 리서치 후, 4명의 페르소나 패널(ai-tech-expert, enterprise-attendee, "
        f"operations-manager, general-attendee)에게 평가를 받고, "
        f"피드백을 반영하여 최종 트렌드 리스트를 확정하세요.\n\n"
        f"각 단계에서 save_discussion 도구로 토론 기록을 저장하세요."
    )

    try:
        result = await _collect_results(
            query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
                    allowed_tools=[
                        "Task",
                        "mcp__conference_tools__save_trend",
                        "mcp__conference_tools__get_trends",
                        "mcp__conference_tools__save_discussion",
                    ],
                    mcp_servers={"conference_tools": conference_tools_server},
                    agents=_build_agents(),
                    permission_mode="bypassPermissions",
                    max_turns=settings.max_agent_turns,
                ),
            )
        )
        logger.info(f"트렌드 리서치 완료 (session={session_id})")
        return result or "리서치 완료"
    except Exception as e:
        logger.error(f"트렌드 리서치 에러 (session={session_id}): {e}")
        raise


async def run_speaker_research(
    topic: str,
    tier: str = "tier3_track",
    count: int = 10,
    preferences: str | None = None,
    session_id: int = 0,
) -> str:
    """연사 추천 + 페르소나 토론 실행."""
    logger.info(f"연사 추천 시작 (session={session_id}, topic={topic})")

    prompt = (
        f"리서치 세션 ID: {session_id}\n\n"
        f"주제: {topic}\n"
        f"티어: {tier}\n"
        f"추천 수: {count}명\n"
    )
    if preferences:
        prompt += f"선호 조건: {preferences}\n"

    prompt += (
        f"\n해외 연사 후보를 발굴하고, 4명의 페르소나 패널에게 다면 평가를 받으세요.\n"
        f"패널 합의를 바탕으로 최종 스코어를 확정하고 DB에 저장하세요.\n"
        f"각 단계에서 save_discussion 도구로 토론 기록을 저장하세요."
    )

    try:
        result = await _collect_results(
            query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
                    allowed_tools=[
                        "Task",
                        "mcp__conference_tools__save_speaker",
                        "mcp__conference_tools__get_speakers",
                        "mcp__conference_tools__score_speaker",
                        "mcp__conference_tools__save_discussion",
                    ],
                    mcp_servers={"conference_tools": conference_tools_server},
                    agents=_build_agents(),
                    permission_mode="bypassPermissions",
                    max_turns=settings.max_agent_turns,
                ),
            )
        )
        logger.info(f"연사 추천 완료 (session={session_id})")
        return result or "연사 추천 완료"
    except Exception as e:
        logger.error(f"연사 추천 에러 (session={session_id}): {e}")
        raise


async def run_daily_scan(session_id: int) -> str:
    """매일 자동 실행되는 트렌드/연사 통합 스캔."""
    from src.prompts.daily_scan import DAILY_SCAN_ORCHESTRATOR_PROMPT

    logger.info(f"일일 스캔 시작 (session={session_id})")

    # 기존 트렌드/연사 목록을 가져와 중복 방지 컨텍스트 구성
    import aiosqlite
    from src.db import queries as q

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

    daily_scan_context = {
        "trends": trends_text,
        "speakers": speakers_text,
    }

    prompt = (
        f"일일 스캔 세션 ID: {session_id}\n\n"
        f"오늘의 자동 스캔을 시작합니다.\n"
        f"1. trend-scanner에게 최신 트렌드 탐색을 요청하세요.\n"
        f"2. speaker-scanner에게 새 연사 후보 탐색을 요청하세요.\n"
        f"3. 페르소나 패널에게 간략한 검증을 받으세요.\n"
        f"4. 모든 결과를 save_daily_suggestion 도구로 저장하세요.\n\n"
        f"각 단계에서 save_discussion 도구로 과정을 기록하세요."
    )

    try:
        result = await _collect_results(
            query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=DAILY_SCAN_ORCHESTRATOR_PROMPT,
                    allowed_tools=[
                        "Task",
                        "mcp__conference_tools__save_daily_suggestion",
                        "mcp__conference_tools__get_trends",
                        "mcp__conference_tools__get_speakers",
                        "mcp__conference_tools__save_discussion",
                    ],
                    mcp_servers={"conference_tools": conference_tools_server},
                    agents=_build_agents(daily_scan_context=daily_scan_context),
                    permission_mode="bypassPermissions",
                    max_turns=settings.max_agent_turns,
                ),
            )
        )
        logger.info(f"일일 스캔 완료 (session={session_id})")
        return result or "일일 스캔 완료"
    except Exception as e:
        logger.error(f"일일 스캔 에러 (session={session_id}): {e}")
        raise


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
        f"필요한 경우 관련 에이전트에게 추가 리서치를 요청하세요.\n"
        f"save_discussion 도구로 처리 과정을 기록하세요."
    )

    try:
        result = await _collect_results(
            query(
                prompt=prompt,
                options=ClaudeAgentOptions(
                    system_prompt=FEEDBACK_PROMPT,
                    allowed_tools=[
                        "Task",
                        "mcp__conference_tools__get_trends",
                        "mcp__conference_tools__get_speakers",
                        "mcp__conference_tools__update_speaker_status",
                        "mcp__conference_tools__save_trend",
                        "mcp__conference_tools__save_speaker",
                        "mcp__conference_tools__save_discussion",
                    ],
                    mcp_servers={"conference_tools": conference_tools_server},
                    agents=_build_agents(),
                    permission_mode="bypassPermissions",
                    max_turns=settings.max_agent_turns,
                ),
            )
        )
        logger.info(f"피드백 처리 완료 (session={session_id})")
        return result or "피드백 처리 완료"
    except Exception as e:
        logger.error(f"피드백 처리 에러 (session={session_id}): {e}")
        raise
