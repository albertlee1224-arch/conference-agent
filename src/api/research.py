"""리서치 실행 API 라우터 — 에이전트 연동."""

import asyncio
import logging
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

import aiosqlite

from src.db.database import get_db
from src.db import queries

logger = logging.getLogger(__name__)

router = APIRouter()


# === Request Models ===


class TrendResearchRequest(BaseModel):
    query: str
    focus_areas: list[str] | None = None


class SpeakerResearchRequest(BaseModel):
    topic: str
    tier: str = "tier3_track"
    count: int = 10
    preferences: str | None = None


# === Background Tasks ===


async def _run_trend_research_bg(session_id: int, query_text: str) -> None:
    """백그라운드에서 트렌드 리서치 에이전트 실행."""
    from src.agents.orchestrator import run_trend_research
    from src.db.database import get_db

    db = await aiosqlite.connect(
        str(__import__("src.config", fromlist=["settings"]).settings.database_path)
    )
    try:
        result = await run_trend_research(query_text, session_id)
        await queries.update_session_status(
            db, session_id, "completed", result_summary=result
        )
    except Exception as e:
        logger.error(f"트렌드 리서치 실패 (session {session_id}): {e}")
        logger.error(traceback.format_exc())
        await queries.update_session_status(
            db, session_id, "failed", result_summary=str(e)
        )
    finally:
        await db.close()


async def _run_speaker_research_bg(
    session_id: int,
    topic: str,
    tier: str,
    count: int,
    preferences: str | None,
) -> None:
    """백그라운드에서 연사 추천 에이전트 실행."""
    from src.agents.orchestrator import run_speaker_research

    db = await aiosqlite.connect(
        str(__import__("src.config", fromlist=["settings"]).settings.database_path)
    )
    try:
        result = await run_speaker_research(
            topic, tier, count, preferences, session_id
        )
        await queries.update_session_status(
            db, session_id, "completed", result_summary=result
        )
    except Exception as e:
        logger.error(f"연사 추천 실패 (session {session_id}): {e}")
        logger.error(traceback.format_exc())
        await queries.update_session_status(
            db, session_id, "failed", result_summary=str(e)
        )
    finally:
        await db.close()


# === Endpoints ===


@router.post("/trends")
async def start_trend_research(
    body: TrendResearchRequest,
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db),
):
    """트렌드 리서치 세션 시작. 에이전트를 백그라운드로 실행."""
    session_id = await queries.create_session(db, "trend", body.query)
    background_tasks.add_task(
        _run_trend_research_bg, session_id, body.query
    )
    return {"session_id": session_id, "status": "running"}


@router.post("/speakers")
async def start_speaker_research(
    body: SpeakerResearchRequest,
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db),
):
    """연사 추천 세션 시작. 에이전트를 백그라운드로 실행."""
    input_query = f"topic={body.topic}, tier={body.tier}, count={body.count}"
    if body.preferences:
        input_query += f", preferences={body.preferences}"

    session_id = await queries.create_session(db, "speaker", input_query)
    background_tasks.add_task(
        _run_speaker_research_bg,
        session_id, body.topic, body.tier, body.count, body.preferences,
    )
    return {"session_id": session_id, "status": "running"}


@router.get("/sessions")
async def list_sessions(
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_sessions(db)


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/discussions")
async def get_discussions(
    session_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """세션의 에이전트 토론 기록 조회."""
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await queries.list_discussions(db, session_id)
