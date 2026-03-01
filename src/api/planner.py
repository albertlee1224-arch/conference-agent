"""Planner Director API 라우터."""

import logging
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends, Query

import aiosqlite

from src.db.database import get_db
from src.db import queries

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_planner_bg(session_id: int) -> None:
    """백그라운드에서 Planner 평가 실행."""
    from src.agents.orchestrator import run_planner_evaluation

    db = await aiosqlite.connect(
        str(__import__("src.config", fromlist=["settings"]).settings.database_path)
    )
    db.row_factory = aiosqlite.Row
    try:
        result = await run_planner_evaluation(session_id)
        await queries.update_session_status(
            db, session_id, "completed", result_summary=result[:500]
        )
    except Exception as e:
        logger.error(f"Planner 평가 실패 (session {session_id}): {e}")
        logger.error(traceback.format_exc())
        await queries.update_session_status(
            db, session_id, "failed", result_summary=str(e)
        )
    finally:
        await db.close()


@router.post("/evaluate")
async def trigger_planner_evaluation(
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Planner 평가를 수동으로 트리거."""
    session_id = await queries.create_session(
        db, "planner", "manual_planner_trigger"
    )
    background_tasks.add_task(_run_planner_bg, session_id)
    return {"session_id": session_id, "status": "running"}


@router.get("/tasks")
async def list_planner_tasks(
    status: str | None = Query(None, description="pending, running, completed, failed"),
    limit: int = Query(50, le=200),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Planner가 생성한 과제 목록 조회."""
    query = "SELECT * FROM planner_tasks WHERE 1=1"
    params: list = []

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
