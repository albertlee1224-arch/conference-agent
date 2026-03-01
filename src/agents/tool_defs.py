"""Anthropic API용 도구 정의 + 핸들러 레지스트리.

orchestrator.py에서 사용하는 모든 커스텀 도구를
Anthropic messages.create() tools 파라미터 형식으로 정의합니다.
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

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

# ── 도구 정의 (Anthropic API 형식) ──────────────────────────

SAVE_TREND_TOOL: dict[str, Any] = {
    "name": "save_trend",
    "description": "트렌드 키워드를 데이터베이스에 저장합니다",
    "input_schema": {
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
}

SAVE_SPEAKER_TOOL: dict[str, Any] = {
    "name": "save_speaker",
    "description": "연사 후보 정보를 데이터베이스에 저장합니다",
    "input_schema": {
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
}

GET_TRENDS_TOOL: dict[str, Any] = {
    "name": "get_trends",
    "description": "저장된 트렌드 목록을 조회합니다",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
        },
    },
}

GET_SPEAKERS_TOOL: dict[str, Any] = {
    "name": "get_speakers",
    "description": "저장된 연사 후보 목록을 조회합니다",
    "input_schema": {
        "type": "object",
        "properties": {
            "tier": {"type": "string"},
            "status": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
        },
    },
}

UPDATE_SPEAKER_STATUS_TOOL: dict[str, Any] = {
    "name": "update_speaker_status",
    "description": "연사 상태를 변경합니다",
    "input_schema": {
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
}

SCORE_SPEAKER_TOOL: dict[str, Any] = {
    "name": "score_speaker",
    "description": "연사 적합성 종합 점수를 계산합니다",
    "input_schema": {
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
}

SAVE_DISCUSSION_TOOL: dict[str, Any] = {
    "name": "save_discussion",
    "description": "에이전트 토론 기록을 저장합니다",
    "input_schema": {
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
}

SAVE_DAILY_SUGGESTION_TOOL: dict[str, Any] = {
    "name": "save_daily_suggestion",
    "description": "일일 자동 스캔에서 발굴한 트렌드/연사 제안을 저장합니다",
    "input_schema": {
        "type": "object",
        "properties": {
            "suggestion_type": {
                "type": "string",
                "enum": ["trend", "speaker"],
                "description": "제안 유형",
            },
            "title": {
                "type": "string",
                "description": "트렌드 키워드 또는 연사 이름 (영문)",
            },
            "summary": {
                "type": "string",
                "description": "왜 새롭고 중요한지 설명 (한국어)",
            },
            "detail_json": {"description": "상세 정보 (JSON 객체 또는 문자열)"},
            "source_urls": {"description": "근거 URL (배열 또는 JSON 문자열)"},
            "relevance_score": {
                "type": "number",
                "description": "적합도 0.0~1.0",
            },
            "session_id": {"type": "integer", "description": "스캔 세션 ID"},
        },
        "required": ["suggestion_type", "title", "summary"],
    },
}

# ── 핸들러 레지스트리 ───────────────────────────────────────

ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]

TOOL_HANDLERS: dict[str, ToolHandler] = {
    "save_trend": save_trend_handler,
    "save_speaker": save_speaker_handler,
    "get_trends": get_trends_handler,
    "get_speakers": get_speakers_handler,
    "update_speaker_status": update_speaker_status_handler,
    "score_speaker": score_speaker_handler,
    "save_discussion": save_discussion_handler,
    "save_daily_suggestion": save_daily_suggestion_handler,
}

# ── 용도별 도구 세트 ────────────────────────────────────────

TREND_RESEARCH_TOOLS = [
    SAVE_TREND_TOOL,
    GET_TRENDS_TOOL,
    SAVE_DISCUSSION_TOOL,
]

SPEAKER_RESEARCH_TOOLS = [
    SAVE_SPEAKER_TOOL,
    GET_SPEAKERS_TOOL,
    SCORE_SPEAKER_TOOL,
    SAVE_DISCUSSION_TOOL,
]

DAILY_SCAN_TOOLS = [
    SAVE_DAILY_SUGGESTION_TOOL,
    GET_TRENDS_TOOL,
    GET_SPEAKERS_TOOL,
    SAVE_DISCUSSION_TOOL,
]

FEEDBACK_TOOLS = [
    GET_TRENDS_TOOL,
    GET_SPEAKERS_TOOL,
    UPDATE_SPEAKER_STATUS_TOOL,
    SAVE_TREND_TOOL,
    SAVE_SPEAKER_TOOL,
    SAVE_DISCUSSION_TOOL,
]

# 페르소나 에이전트용 (토론 기록만)
PERSONA_TOOLS = [
    SAVE_DISCUSSION_TOOL,
]
