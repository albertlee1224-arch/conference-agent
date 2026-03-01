"""연사 스코어링 도구."""

from __future__ import annotations

from typing import Any


async def score_speaker_handler(args: dict[str, Any]) -> dict[str, Any]:
    """연사 적합성 종합 점수 계산.

    가중치:
    - expertise: 0.30 (전문성)
    - name_value: 0.25 (네임밸류)
    - speaking: 0.20 (강연 이력)
    - relevance: 0.25 (행사 적합도)
    """
    weights = {
        "expertise": 0.30,
        "name_value": 0.25,
        "speaking": 0.20,
        "relevance": 0.25,
    }

    expertise = args.get("expertise_score", 0.0)
    name_value = args.get("name_value_score", 0.0)
    speaking = args.get("speaking_score", 0.0)
    relevance = args.get("relevance_score", 0.0)

    overall = (
        expertise * weights["expertise"]
        + name_value * weights["name_value"]
        + speaking * weights["speaking"]
        + relevance * weights["relevance"]
    )

    # 티어 판단
    if overall >= 0.8 and name_value >= 0.8:
        tier = "tier1_keynote"
        tier_label = "Tier 1 (오전 키노트)"
    elif overall >= 0.5 and expertise >= 0.7:
        tier = "tier3_track"
        tier_label = "Tier 3 (오후 트랙)"
    else:
        tier = "unassigned"
        tier_label = "미배정"

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"종합 점수: {overall:.2f}\n"
                    f"  - 전문성: {expertise:.2f} (×{weights['expertise']})\n"
                    f"  - 네임밸류: {name_value:.2f} (×{weights['name_value']})\n"
                    f"  - 강연이력: {speaking:.2f} (×{weights['speaking']})\n"
                    f"  - 적합도: {relevance:.2f} (×{weights['relevance']})\n"
                    f"추천 티어: {tier_label} ({tier})"
                ),
            }
        ]
    }
