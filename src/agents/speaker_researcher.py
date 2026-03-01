"""연사 추천 에이전트 정의."""

from src.prompts.speaker_research import SPEAKER_RESEARCH_PROMPT

SPEAKER_RESEARCHER_AGENT = {
    "description": (
        "해외 연사 후보를 발굴하고 프로필을 수집하여 "
        "적합성을 스코어링하는 에이전트. 연사 리서치 전문."
    ),
    "prompt": SPEAKER_RESEARCH_PROMPT,
    "tools": [
        "WebSearch",
        "WebFetch",
        "mcp__conference_tools__save_speaker",
        "mcp__conference_tools__score_speaker",
    ],
    "model": "sonnet",
}
