"""4개 페르소나 에이전트 정의."""

from src.prompts.personas import (
    AI_TECH_EXPERT_PROMPT,
    ENTERPRISE_ATTENDEE_PROMPT,
    GENERAL_ATTENDEE_PROMPT,
    OPERATIONS_MANAGER_PROMPT,
)

# 페르소나 에이전트 설정
# AgentDefinition 형태로 Orchestrator에서 사용
PERSONA_AGENTS = {
    "ai-tech-expert": {
        "description": "AI 기술 전문가 — 트렌드/연사의 기술적 타당성, 최신성, 깊이를 평가",
        "prompt": AI_TECH_EXPERT_PROMPT,
        "tools": ["WebSearch"],
        "model": "sonnet",
    },
    "enterprise-attendee": {
        "description": "대기업 참가자 — 비즈니스 가치, ROI, 100만원 티켓 정당성을 평가",
        "prompt": ENTERPRISE_ATTENDEE_PROMPT,
        "tools": [],
        "model": "sonnet",
    },
    "operations-manager": {
        "description": "오퍼레이션 담당자 — 섭외 현실성, 비용, 일정, 비자, 통역 등 실행 가능성 평가",
        "prompt": OPERATIONS_MANAGER_PROMPT,
        "tools": ["WebSearch"],
        "model": "sonnet",
    },
    "general-attendee": {
        "description": "일반 참가자 — 세션 흥미도, 접근성, 이해 가능성, SNS 공유 가치 평가",
        "prompt": GENERAL_ATTENDEE_PROMPT,
        "tools": [],
        "model": "sonnet",
    },
}

PERSONA_NAMES = list(PERSONA_AGENTS.keys())
