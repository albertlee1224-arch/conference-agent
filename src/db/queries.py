"""SQL 쿼리 함수 — 모든 쿼리에 파라미터 바인딩 적용."""

from __future__ import annotations

import json
from typing import Any

import aiosqlite


# === Research Sessions ===


async def create_session(
    db: aiosqlite.Connection,
    session_type: str,
    input_query: str,
) -> int:
    cursor = await db.execute(
        "INSERT INTO research_sessions (session_type, input_query) VALUES (?, ?)",
        (session_type, input_query),
    )
    await db.commit()
    return cursor.lastrowid


async def update_session_status(
    db: aiosqlite.Connection,
    session_id: int,
    status: str,
    result_summary: str | None = None,
    agent_session_id: str | None = None,
) -> None:
    await db.execute(
        """UPDATE research_sessions
           SET status = ?, result_summary = ?, agent_session_id = ?,
               completed_at = CASE WHEN ? IN ('completed', 'failed')
                              THEN datetime('now') ELSE completed_at END
           WHERE id = ?""",
        (status, result_summary, agent_session_id, status, session_id),
    )
    await db.commit()


async def get_session(db: aiosqlite.Connection, session_id: int) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM research_sessions WHERE id = ?", (session_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def list_sessions(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM research_sessions ORDER BY created_at DESC"
    )
    return [dict(row) for row in await cursor.fetchall()]


# === Trends ===


async def insert_trend(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "keyword", "category", "description", "evidence",
        "source_conferences", "relevance_score", "is_auto_discovered", "session_id",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))
    values = list(present.values())

    cursor = await db.execute(
        f"INSERT INTO trends ({cols}) VALUES ({placeholders})", values
    )
    await db.commit()
    return cursor.lastrowid


async def list_trends(
    db: aiosqlite.Connection,
    category: str | None = None,
    min_relevance: float | None = None,
) -> list[dict]:
    query = "SELECT * FROM trends WHERE 1=1"
    params: list[Any] = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if min_relevance is not None:
        query += " AND relevance_score >= ?"
        params.append(min_relevance)

    query += " ORDER BY relevance_score DESC"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def get_trend(db: aiosqlite.Connection, trend_id: int) -> dict | None:
    cursor = await db.execute("SELECT * FROM trends WHERE id = ?", (trend_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


# === Tracks ===


async def insert_track(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = ["name", "description", "target_audience", "session_format", "sort_order"]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO tracks ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_tracks(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT * FROM tracks ORDER BY sort_order")
    return [dict(row) for row in await cursor.fetchall()]


async def get_track(db: aiosqlite.Connection, track_id: int) -> dict | None:
    cursor = await db.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_track(
    db: aiosqlite.Connection, track_id: int, **kwargs: Any
) -> None:
    fields = ["name", "description", "target_audience", "session_format", "sort_order"]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    if not present:
        return

    set_clause = ", ".join(f"{k} = ?" for k in present)
    values = list(present.values()) + [track_id]

    await db.execute(
        f"UPDATE tracks SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    await db.commit()


async def set_track_trends(
    db: aiosqlite.Connection, track_id: int, trend_ids: list[int]
) -> None:
    await db.execute("DELETE FROM track_trends WHERE track_id = ?", (track_id,))
    for tid in trend_ids:
        await db.execute(
            "INSERT INTO track_trends (track_id, trend_id) VALUES (?, ?)",
            (track_id, tid),
        )
    await db.commit()


async def get_track_trends(
    db: aiosqlite.Connection, track_id: int
) -> list[dict]:
    cursor = await db.execute(
        """SELECT t.* FROM trends t
           JOIN track_trends tt ON t.id = tt.trend_id
           WHERE tt.track_id = ?""",
        (track_id,),
    )
    return [dict(row) for row in await cursor.fetchall()]


# === Speakers ===


async def insert_speaker(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "name", "name_ko", "title", "organization", "country", "bio",
        "expertise", "tier", "overall_score", "expertise_score",
        "name_value_score", "speaking_score", "relevance_score",
        "linkedin_url", "website_url", "email", "photo_url",
        "speaking_history", "publications", "recommendation_reason",
        "source_channel", "is_auto_discovered", "status", "track_id", "session_id", "team_notes",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO speakers ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_speakers(
    db: aiosqlite.Connection,
    status: str | None = None,
    tier: str | None = None,
    track_id: int | None = None,
    sort_by: str = "overall_score",
    limit: int = 50,
) -> list[dict]:
    allowed_sort = {"overall_score", "name", "created_at", "relevance_score"}
    if sort_by not in allowed_sort:
        sort_by = "overall_score"

    query = "SELECT * FROM speakers WHERE 1=1"
    params: list[Any] = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if tier:
        query += " AND tier = ?"
        params.append(tier)
    if track_id is not None:
        query += " AND track_id = ?"
        params.append(track_id)

    query += f" ORDER BY {sort_by} DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def get_speaker(db: aiosqlite.Connection, speaker_id: int) -> dict | None:
    cursor = await db.execute("SELECT * FROM speakers WHERE id = ?", (speaker_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_speaker(
    db: aiosqlite.Connection, speaker_id: int, **kwargs: Any
) -> None:
    fields = [
        "status", "tier", "track_id", "team_notes", "overall_score",
        "expertise_score", "name_value_score", "speaking_score", "relevance_score",
        "estimated_fee", "risk_level", "assigned_to", "travel_required", "last_contacted_at",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    if not present:
        return

    set_clause = ", ".join(f"{k} = ?" for k in present)
    values = list(present.values()) + [speaker_id]

    await db.execute(
        f"UPDATE speakers SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    await db.commit()


async def delete_speaker(db: aiosqlite.Connection, speaker_id: int) -> bool:
    cursor = await db.execute("DELETE FROM speakers WHERE id = ?", (speaker_id,))
    await db.commit()
    return cursor.rowcount > 0


# === Feedback ===


async def insert_feedback(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "feedback_type", "content", "target_id", "target_type",
        "action_taken", "session_id", "created_by",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO feedback ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_feedback(
    db: aiosqlite.Connection,
    target_type: str | None = None,
    target_id: int | None = None,
) -> list[dict]:
    query = "SELECT * FROM feedback WHERE 1=1"
    params: list[Any] = []

    if target_type:
        query += " AND target_type = ?"
        params.append(target_type)
    if target_id is not None:
        query += " AND target_id = ?"
        params.append(target_id)

    query += " ORDER BY created_at DESC"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


# === Discussions ===


async def insert_discussion(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = ["session_id", "agent_name", "message_type", "content", "round_number"]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO discussions ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_discussions(
    db: aiosqlite.Connection, session_id: int
) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM discussions WHERE session_id = ? ORDER BY round_number, id",
        (session_id,),
    )
    return [dict(row) for row in await cursor.fetchall()]


# === Daily Suggestions ===


async def insert_suggestion(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "suggestion_date", "suggestion_type", "title", "summary",
        "detail_json", "source_urls", "relevance_score", "session_id",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO daily_suggestions ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_suggestions(
    db: aiosqlite.Connection,
    date: str | None = None,
    suggestion_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    query = "SELECT * FROM daily_suggestions WHERE 1=1"
    params: list[Any] = []

    if date:
        query += " AND suggestion_date = ?"
        params.append(date)
    if suggestion_type:
        query += " AND suggestion_type = ?"
        params.append(suggestion_type)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY relevance_score DESC, created_at DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def get_suggestion(db: aiosqlite.Connection, suggestion_id: int) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM daily_suggestions WHERE id = ?", (suggestion_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_suggestion_status(
    db: aiosqlite.Connection,
    suggestion_id: int,
    status: str,
    reviewed_by: str | None = None,
    linked_trend_id: int | None = None,
    linked_speaker_id: int | None = None,
) -> None:
    await db.execute(
        """UPDATE daily_suggestions
           SET status = ?, reviewed_by = ?, reviewed_at = datetime('now'),
               linked_trend_id = COALESCE(?, linked_trend_id),
               linked_speaker_id = COALESCE(?, linked_speaker_id)
           WHERE id = ?""",
        (status, reviewed_by, linked_trend_id, linked_speaker_id, suggestion_id),
    )
    await db.commit()


async def get_today_suggestion_count(db: aiosqlite.Connection) -> int:
    cursor = await db.execute(
        "SELECT COUNT(*) FROM daily_suggestions WHERE suggestion_date = date('now')"
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def get_suggestion_stats(
    db: aiosqlite.Connection, date: str | None = None
) -> dict:
    target_date = date or "date('now')"
    if date:
        cursor = await db.execute(
            """SELECT
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'pending_review' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN status = 'dismissed' THEN 1 ELSE 0 END) as dismissed
               FROM daily_suggestions WHERE suggestion_date = ?""",
            (date,),
        )
    else:
        cursor = await db.execute(
            """SELECT
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'pending_review' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN status = 'dismissed' THEN 1 ELSE 0 END) as dismissed
               FROM daily_suggestions WHERE suggestion_date = date('now')"""
        )
    row = await cursor.fetchone()
    if row:
        return {
            "total": row[0] or 0,
            "pending": row[1] or 0,
            "approved": row[2] or 0,
            "dismissed": row[3] or 0,
        }
    return {"total": 0, "pending": 0, "approved": 0, "dismissed": 0}


# === Agenda Sessions ===


async def insert_agenda_session(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "title", "day", "track_id", "start_time", "end_time",
        "session_type", "speaker_id", "second_speaker_id", "moderator_id",
        "description", "notes", "status", "sort_order",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO agenda_sessions ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_agenda_sessions(
    db: aiosqlite.Connection,
    day: int | None = None,
    track_id: int | None = None,
) -> list[dict]:
    query = "SELECT * FROM agenda_sessions WHERE 1=1"
    params: list[Any] = []

    if day is not None:
        query += " AND day = ?"
        params.append(day)
    if track_id is not None:
        query += " AND track_id = ?"
        params.append(track_id)

    query += " ORDER BY day, start_time, sort_order"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def get_agenda_session(db: aiosqlite.Connection, session_id: int) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM agenda_sessions WHERE id = ?", (session_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_agenda_session(
    db: aiosqlite.Connection, session_id: int, **kwargs: Any
) -> None:
    fields = [
        "title", "day", "track_id", "start_time", "end_time",
        "session_type", "speaker_id", "second_speaker_id", "moderator_id",
        "description", "notes", "status", "sort_order",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    if not present:
        return

    set_clause = ", ".join(f"{k} = ?" for k in present)
    values = list(present.values()) + [session_id]

    await db.execute(
        f"UPDATE agenda_sessions SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    await db.commit()


async def delete_agenda_session(db: aiosqlite.Connection, session_id: int) -> bool:
    cursor = await db.execute(
        "DELETE FROM agenda_sessions WHERE id = ?", (session_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


# === Milestones ===


async def insert_milestone(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "title", "description", "due_date", "phase",
        "status", "owner", "sort_order",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO milestones ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_milestones(
    db: aiosqlite.Connection,
    phase: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM milestones WHERE 1=1"
    params: list[Any] = []

    if phase:
        query += " AND phase = ?"
        params.append(phase)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY due_date, sort_order"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def update_milestone(
    db: aiosqlite.Connection, milestone_id: int, **kwargs: Any
) -> None:
    fields = [
        "title", "description", "due_date", "phase",
        "status", "owner", "sort_order", "completed_at",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    if not present:
        return

    set_clause = ", ".join(f"{k} = ?" for k in present)
    values = list(present.values()) + [milestone_id]

    await db.execute(
        f"UPDATE milestones SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    await db.commit()


async def delete_milestone(db: aiosqlite.Connection, milestone_id: int) -> bool:
    cursor = await db.execute(
        "DELETE FROM milestones WHERE id = ?", (milestone_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


# === Budget Items ===


async def insert_budget_item(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "category", "description", "estimated_amount", "actual_amount",
        "currency", "speaker_id", "notes", "status",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO budget_items ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_budget_items(
    db: aiosqlite.Connection,
    category: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM budget_items WHERE 1=1"
    params: list[Any] = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def get_budget_summary(db: aiosqlite.Connection) -> dict:
    cursor = await db.execute(
        """SELECT
               category,
               SUM(estimated_amount) as estimated,
               SUM(COALESCE(actual_amount, 0)) as actual,
               COUNT(*) as count
           FROM budget_items
           GROUP BY category"""
    )
    rows = [dict(row) for row in await cursor.fetchall()]

    total_est = sum(r["estimated"] or 0 for r in rows)
    total_act = sum(r["actual"] or 0 for r in rows)
    return {
        "by_category": rows,
        "total_estimated": total_est,
        "total_actual": total_act,
        "utilization": total_act / total_est if total_est > 0 else 0,
    }


async def update_budget_item(
    db: aiosqlite.Connection, item_id: int, **kwargs: Any
) -> None:
    fields = [
        "category", "description", "estimated_amount", "actual_amount",
        "currency", "speaker_id", "notes", "status",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    if not present:
        return

    set_clause = ", ".join(f"{k} = ?" for k in present)
    values = list(present.values()) + [item_id]

    await db.execute(
        f"UPDATE budget_items SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    await db.commit()


async def delete_budget_item(db: aiosqlite.Connection, item_id: int) -> bool:
    cursor = await db.execute(
        "DELETE FROM budget_items WHERE id = ?", (item_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


# === Speaker Contacts ===


async def insert_speaker_contact(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "speaker_id", "contact_type", "direction", "subject",
        "content", "contacted_by", "contact_date", "follow_up_date", "status",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO speaker_contacts ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_speaker_contacts(
    db: aiosqlite.Connection,
    speaker_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM speaker_contacts WHERE 1=1"
    params: list[Any] = []

    if speaker_id is not None:
        query += " AND speaker_id = ?"
        params.append(speaker_id)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY contact_date DESC"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]


async def update_speaker_contact(
    db: aiosqlite.Connection, contact_id: int, **kwargs: Any
) -> None:
    fields = ["status", "content", "follow_up_date", "contacted_by"]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    if not present:
        return

    set_clause = ", ".join(f"{k} = ?" for k in present)
    values = list(present.values()) + [contact_id]

    await db.execute(
        f"UPDATE speaker_contacts SET {set_clause} WHERE id = ?",
        values,
    )
    await db.commit()


async def get_follow_up_alerts(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        """SELECT sc.*, s.name as speaker_name, s.organization as speaker_org
           FROM speaker_contacts sc
           JOIN speakers s ON sc.speaker_id = s.id
           WHERE sc.status IN ('sent', 'no_response', 'follow_up_needed')
             AND sc.follow_up_date <= date('now')
           ORDER BY sc.follow_up_date"""
    )
    return [dict(row) for row in await cursor.fetchall()]


# === Planner Tasks ===


async def insert_planner_task(db: aiosqlite.Connection, **kwargs: Any) -> int:
    fields = [
        "task_type", "priority", "query", "reason", "status", "session_id",
    ]
    present = {k: v for k, v in kwargs.items() if k in fields and v is not None}
    cols = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))

    cursor = await db.execute(
        f"INSERT INTO planner_tasks ({cols}) VALUES ({placeholders})",
        list(present.values()),
    )
    await db.commit()
    return cursor.lastrowid


async def list_planner_tasks(
    db: aiosqlite.Connection,
    status: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM planner_tasks WHERE 1=1"
    params: list[Any] = []

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"
    cursor = await db.execute(query, params)
    return [dict(row) for row in await cursor.fetchall()]
