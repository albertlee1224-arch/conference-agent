"""Anthropic SDK 기반 에이전트 루프.

messages.create() → tool_use 처리 → tool_result 추가를 반복하는 범용 agentic loop.
claude-agent-sdk 없이 서버 환경에서도 동작합니다.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Awaitable

import anthropic

from src.config import settings

logger = logging.getLogger(__name__)

# Anthropic 내장 웹 검색 도구 (별도 handler 불필요 — API가 자동 처리)
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 10,
}

# 핸들러 타입: tool_name → async handler(args) → str
ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    """싱글턴 Anthropic 클라이언트."""
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def run_agent(
    *,
    system_prompt: str,
    user_prompt: str,
    tools: list[dict[str, Any]],
    tool_handlers: dict[str, ToolHandler],
    model: str = "claude-sonnet-4-20250514",
    max_turns: int = 30,
    max_tokens: int = 8192,
) -> str:
    """범용 에이전트 루프.

    Args:
        system_prompt: 시스템 프롬프트.
        user_prompt: 사용자 메시지 (에이전트에게 주는 지시).
        tools: Anthropic API tool 스키마 리스트 (커스텀 + web_search 등).
        tool_handlers: {tool_name: async handler} 맵. web_search은 포함 불필요.
        model: 사용할 Claude 모델 ID.
        max_turns: 최대 루프 반복 횟수.
        max_tokens: 응답 최대 토큰.

    Returns:
        최종 텍스트 응답.
    """
    client = _get_client()
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    for turn in range(max_turns):
        logger.debug(f"Agent turn {turn + 1}/{max_turns}")

        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            tools=tools,
        )

        # 응답을 assistant 메시지로 추가
        messages.append({"role": "assistant", "content": response.content})

        # stop_reason 확인
        if response.stop_reason == "end_turn":
            break

        # tool_use 블록 처리
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input

            logger.info(f"Tool call: {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:200]})")

            handler = tool_handlers.get(tool_name)
            if handler:
                try:
                    result_text = await handler(tool_input)
                except Exception as e:
                    logger.error(f"Tool error ({tool_name}): {e}")
                    result_text = f"오류: {e}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })
            else:
                # web_search 등 Anthropic 내장 도구는 handler 없이 자동 처리됨
                # server_tool_use → server_tool_result 로 자동 포함됨
                logger.debug(f"No handler for {tool_name} (likely built-in)")

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        elif response.stop_reason != "end_turn":
            # tool_use가 있었지만 모두 내장 도구인 경우 — 다음 턴 진행
            # server_tool_use/server_tool_result는 content에 자동 포함되어 있음
            pass

    # 최종 텍스트 추출
    text_parts: list[str] = []
    for block in response.content:
        if hasattr(block, "text"):
            text_parts.append(block.text)

    result = "\n".join(text_parts) if text_parts else "에이전트 실행 완료"
    logger.info(f"Agent finished after {turn + 1} turns, result length: {len(result)}")
    return result
