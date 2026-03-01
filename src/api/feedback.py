"""피드백 API 라우터 — 에이전트 연동."""

import logging
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends

import aiosqlite

from src.db.database import get_db
from src.db.models import FeedbackCreate
from src.db import queries

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_feedback_processing_bg(
    session_id: int,
    feedback_content: str,
    feedback_type: str,
    feedback_id: int,
) -> None:
    """백그라운드에서 피드백 처리 에이전트 실행."""
    from src.agents.orchestrator import run_feedback_processing

    db = await aiosqlite.connect(
        str(__import__("src.config", fromlist=["settings"]).settings.database_path)
    )
    try:
        result = await run_feedback_processing(
            feedback_content, feedback_type, session_id
        )
        # 피드백에 조치 결과 기록
        await db.execute(
            "UPDATE feedback SET action_taken = ?, session_id = ? WHERE id = ?",
            (result, session_id, feedback_id),
        )
        await queries.update_session_status(
            db, session_id, "completed", result_summary=result
        )
        await db.commit()
    except Exception as e:
        logger.error(f"피드백 처리 실패 (session {session_id}): {e}")
        logger.error(traceback.format_exc())
        await queries.update_session_status(
            db, session_id, "failed", result_summary=str(e)
        )
    finally:
        await db.close()


@router.post("", status_code=201)
async def create_feedback(
    body: FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db),
):
    """피드백 저장 + 에이전트로 분석/반영."""
    feedback_id = await queries.insert_feedback(
        db, **body.model_dump(exclude_none=True)
    )

    # 피드백 처리 세션 생성
    session_id = await queries.create_session(
        db, "feedback", body.content
    )

    background_tasks.add_task(
        _run_feedback_processing_bg,
        session_id, body.content, body.feedback_type, feedback_id,
    )

    return {
        "id": feedback_id,
        "session_id": session_id,
        "status": "processing",
    }


@router.get("/history")
async def list_feedback(
    target_type: str | None = None,
    target_id: int | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_feedback(
        db, target_type=target_type, target_id=target_id
    )
