"""일일 제안 관리 API 라우터."""

import json
import logging
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

import aiosqlite

from src.db.database import get_db
from src.db import queries
from src.db.models import DailySuggestionUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


# === Background Task ===


async def _run_daily_scan_bg(session_id: int) -> None:
    """백그라운드에서 일일 스캔 에이전트 실행."""
    from src.agents.orchestrator import run_daily_scan

    db = await aiosqlite.connect(
        str(__import__("src.config", fromlist=["settings"]).settings.database_path)
    )
    db.row_factory = aiosqlite.Row
    try:
        result = await run_daily_scan(session_id)
        await queries.update_session_status(
            db, session_id, "completed", result_summary=result
        )
    except Exception as e:
        logger.error(f"일일 스캔 실패 (session {session_id}): {e}")
        logger.error(traceback.format_exc())
        await queries.update_session_status(
            db, session_id, "failed", result_summary=str(e)
        )
    finally:
        await db.close()


# === Endpoints ===


@router.get("")
async def list_suggestions(
    date: str | None = Query(None, description="날짜 (YYYY-MM-DD)"),
    suggestion_type: str | None = Query(None, description="trend 또는 speaker"),
    status: str | None = Query(None, description="pending_review, approved, dismissed"),
    limit: int = Query(50, le=200),
    db: aiosqlite.Connection = Depends(get_db),
):
    """일일 제안 목록 조회."""
    return await queries.list_suggestions(
        db, date=date, suggestion_type=suggestion_type,
        status=status, limit=limit,
    )


@router.get("/stats")
async def suggestion_stats(
    date: str | None = Query(None, description="날짜 (YYYY-MM-DD)"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """제안 통계 (대기/승인/거절 수)."""
    return await queries.get_suggestion_stats(db, date=date)


@router.post("/scan")
async def trigger_daily_scan(
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db),
):
    """일일 스캔을 수동으로 트리거."""
    session_id = await queries.create_session(
        db, "daily_scan", "manual_trigger"
    )
    background_tasks.add_task(_run_daily_scan_bg, session_id)
    return {"session_id": session_id, "status": "running"}


@router.patch("/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: int,
    body: DailySuggestionUpdate | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    """제안을 승인 → trends 또는 speakers 테이블에 추가."""
    suggestion = await queries.get_suggestion(db, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion["status"] != "pending_review":
        raise HTTPException(status_code=400, detail="이미 처리된 제안입니다")

    reviewed_by = body.reviewed_by if body else "team"

    linked_trend_id = None
    linked_speaker_id = None

    if suggestion["suggestion_type"] == "trend":
        # 트렌드로 저장
        detail = {}
        if suggestion.get("detail_json"):
            try:
                detail = json.loads(suggestion["detail_json"])
            except json.JSONDecodeError:
                pass

        evidence = detail.get("evidence")
        if isinstance(evidence, list):
            evidence = json.dumps(evidence, ensure_ascii=False)

        linked_trend_id = await queries.insert_trend(
            db,
            keyword=suggestion["title"],
            category=detail.get("category"),
            description=suggestion.get("summary"),
            evidence=evidence,
            relevance_score=suggestion.get("relevance_score"),
            is_auto_discovered=1,
        )

    elif suggestion["suggestion_type"] == "speaker":
        # 연사로 저장
        detail = {}
        if suggestion.get("detail_json"):
            try:
                detail = json.loads(suggestion["detail_json"])
            except json.JSONDecodeError:
                pass

        scores = detail.get("scores", {})
        expertise_list = detail.get("expertise")
        if isinstance(expertise_list, list):
            expertise_list = json.dumps(expertise_list, ensure_ascii=False)

        linked_speaker_id = await queries.insert_speaker(
            db,
            name=suggestion["title"],
            organization=detail.get("organization"),
            title=detail.get("title"),
            country=detail.get("country"),
            expertise=expertise_list,
            linkedin_url=detail.get("linkedin_url"),
            recommendation_reason=suggestion.get("summary"),
            overall_score=suggestion.get("relevance_score"),
            expertise_score=scores.get("expertise_score"),
            name_value_score=scores.get("name_value_score"),
            speaking_score=scores.get("speaking_score"),
            relevance_score=scores.get("relevance_score"),
            source_channel="daily_scan",
            is_auto_discovered=1,
        )

    # 제안 상태 업데이트
    await queries.update_suggestion_status(
        db, suggestion_id, "approved",
        reviewed_by=reviewed_by,
        linked_trend_id=linked_trend_id,
        linked_speaker_id=linked_speaker_id,
    )

    return {
        "status": "approved",
        "suggestion_id": suggestion_id,
        "linked_trend_id": linked_trend_id,
        "linked_speaker_id": linked_speaker_id,
    }


@router.patch("/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: int,
    body: DailySuggestionUpdate | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    """제안을 거절."""
    suggestion = await queries.get_suggestion(db, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion["status"] != "pending_review":
        raise HTTPException(status_code=400, detail="이미 처리된 제안입니다")

    reviewed_by = body.reviewed_by if body else "team"

    await queries.update_suggestion_status(
        db, suggestion_id, "dismissed", reviewed_by=reviewed_by,
    )

    return {"status": "dismissed", "suggestion_id": suggestion_id}
