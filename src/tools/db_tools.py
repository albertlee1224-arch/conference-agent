"""에이전트용 DB 커스텀 도구 — @tool 데코레이터 기반."""

from __future__ import annotations

import json
from typing import Any

import aiosqlite

from src.config import settings


async def _get_connection() -> aiosqlite.Connection:
    """에이전트 도구 내부용 DB 연결."""
    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def save_trend_handler(args: dict[str, Any]) -> dict[str, Any]:
    """트렌드를 DB에 저장."""
    db = await _get_connection()
    try:
        evidence = args.get("evidence")
        if isinstance(evidence, list):
            evidence = json.dumps(evidence, ensure_ascii=False)

        source_conferences = args.get("source_conferences")
        if isinstance(source_conferences, list):
            source_conferences = json.dumps(source_conferences, ensure_ascii=False)

        cursor = await db.execute(
            """INSERT INTO trends
               (keyword, category, description, evidence,
                source_conferences, relevance_score, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                args["keyword"],
                args.get("category"),
                args.get("description"),
                evidence,
                source_conferences,
                args.get("relevance_score"),
                args.get("session_id"),
            ),
        )
        await db.commit()
        trend_id = cursor.lastrowid
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"트렌드 '{args['keyword']}' 저장 완료 (ID: {trend_id})",
                }
            ]
        }
    finally:
        await db.close()


async def save_speaker_handler(args: dict[str, Any]) -> dict[str, Any]:
    """연사 후보를 DB에 저장."""
    db = await _get_connection()
    try:
        expertise = args.get("expertise")
        if isinstance(expertise, list):
            expertise = json.dumps(expertise, ensure_ascii=False)

        speaking_history = args.get("speaking_history")
        if isinstance(speaking_history, list):
            speaking_history = json.dumps(speaking_history, ensure_ascii=False)

        publications = args.get("publications")
        if isinstance(publications, list):
            publications = json.dumps(publications, ensure_ascii=False)

        # 티어 자동 판단
        overall = args.get("overall_score", 0)
        name_value = args.get("name_value_score", 0)
        expertise_s = args.get("expertise_score", 0)
        tier = args.get("tier", "unassigned")
        if tier == "unassigned":
            if overall >= 0.8 and name_value >= 0.8:
                tier = "tier1_keynote"
            elif overall >= 0.5 and expertise_s >= 0.7:
                tier = "tier3_track"

        cursor = await db.execute(
            """INSERT INTO speakers
               (name, name_ko, title, organization, country, bio,
                expertise, tier, overall_score, expertise_score,
                name_value_score, speaking_score, relevance_score,
                linkedin_url, website_url, speaking_history, publications,
                recommendation_reason, source_channel, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                args["name"],
                args.get("name_ko"),
                args.get("title"),
                args.get("organization"),
                args.get("country"),
                args.get("bio"),
                expertise,
                tier,
                overall,
                expertise_s,
                name_value,
                args.get("speaking_score", 0),
                args.get("relevance_score", 0),
                args.get("linkedin_url"),
                args.get("website_url"),
                speaking_history,
                publications,
                args.get("recommendation_reason"),
                args.get("source_channel"),
                args.get("session_id"),
            ),
        )
        await db.commit()
        speaker_id = cursor.lastrowid
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"연사 '{args['name']}' ({args.get('organization', 'N/A')}) "
                        f"저장 완료 (ID: {speaker_id}, Tier: {tier})"
                    ),
                }
            ]
        }
    finally:
        await db.close()


async def get_trends_handler(args: dict[str, Any]) -> dict[str, Any]:
    """저장된 트렌드 목록 조회."""
    db = await _get_connection()
    try:
        query = "SELECT * FROM trends WHERE 1=1"
        params: list[Any] = []

        if args.get("category"):
            query += " AND category = ?"
            params.append(args["category"])

        query += " ORDER BY relevance_score DESC LIMIT ?"
        params.append(args.get("limit", 20))

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        trends = [dict(row) for row in rows]

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(trends, ensure_ascii=False, indent=2),
                }
            ]
        }
    finally:
        await db.close()


async def get_speakers_handler(args: dict[str, Any]) -> dict[str, Any]:
    """저장된 연사 후보 목록 조회."""
    db = await _get_connection()
    try:
        query = "SELECT * FROM speakers WHERE 1=1"
        params: list[Any] = []

        if args.get("tier"):
            query += " AND tier = ?"
            params.append(args["tier"])
        if args.get("status"):
            query += " AND status = ?"
            params.append(args["status"])

        query += " ORDER BY overall_score DESC LIMIT ?"
        params.append(args.get("limit", 20))

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        speakers = [dict(row) for row in rows]

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(speakers, ensure_ascii=False, indent=2),
                }
            ]
        }
    finally:
        await db.close()


async def update_speaker_status_handler(args: dict[str, Any]) -> dict[str, Any]:
    """연사 상태 변경."""
    db = await _get_connection()
    try:
        await db.execute(
            "UPDATE speakers SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (args["status"], args["speaker_id"]),
        )
        await db.commit()
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"연사 ID {args['speaker_id']} 상태 → {args['status']}",
                }
            ]
        }
    finally:
        await db.close()


async def save_discussion_handler(args: dict[str, Any]) -> dict[str, Any]:
    """에이전트 토론 기록 저장."""
    db = await _get_connection()
    try:
        cursor = await db.execute(
            """INSERT INTO discussions
               (session_id, agent_name, message_type, content, round_number)
               VALUES (?, ?, ?, ?, ?)""",
            (
                args["session_id"],
                args["agent_name"],
                args["message_type"],
                args["content"],
                args.get("round_number", 1),
            ),
        )
        await db.commit()
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"토론 기록 저장 (ID: {cursor.lastrowid})",
                }
            ]
        }
    finally:
        await db.close()


async def save_daily_suggestion_handler(args: dict[str, Any]) -> dict[str, Any]:
    """일일 자동 스캔 제안 저장."""
    from datetime import date

    db = await _get_connection()
    try:
        source_urls = args.get("source_urls")
        if isinstance(source_urls, list):
            source_urls = json.dumps(source_urls, ensure_ascii=False)

        cursor = await db.execute(
            """INSERT INTO daily_suggestions
               (suggestion_date, suggestion_type, title, summary,
                detail_json, source_urls, relevance_score, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                date.today().isoformat(),
                args["suggestion_type"],
                args["title"],
                args.get("summary"),
                args.get("detail_json"),
                source_urls,
                args.get("relevance_score"),
                args.get("session_id"),
            ),
        )
        await db.commit()
        suggestion_id = cursor.lastrowid
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"제안 저장 완료 — [{args['suggestion_type']}] "
                        f"'{args['title']}' (ID: {suggestion_id})"
                    ),
                }
            ]
        }
    finally:
        await db.close()
