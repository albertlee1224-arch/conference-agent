"""트렌드 리서치 에이전트 정의."""

from src.prompts.trend_research import TREND_RESEARCH_PROMPT

TREND_RESEARCHER_AGENT = {
    "description": (
        "AI 컨퍼런스 트렌드를 웹에서 리서치하고 "
        "DB에 저장하는 에이전트. 최신 AI 트렌드 분석 전문."
    ),
    "prompt": TREND_RESEARCH_PROMPT,
    "tools": [
        "WebSearch",
        "WebFetch",
        "mcp__conference_tools__save_trend",
    ],
    "model": "sonnet",
}
