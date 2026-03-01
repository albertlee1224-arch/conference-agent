"""APScheduler 기반 일일 자동 스캔 스케줄러."""

from __future__ import annotations

import logging
import traceback

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_planner_evaluation() -> None:
    """Planner Director: DB 데이터 품질 평가 + 자동 개선."""
    from src.agents.orchestrator import run_planner_evaluation
    from src.db import queries

    if not settings.planner_enabled:
        return

    logger.info("Planner 평가 스케줄 시작")

    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")

    try:
        session_id = await queries.create_session(
            db, "planner", "scheduled_planner_evaluation"
        )
        try:
            result = await run_planner_evaluation(session_id)
            await queries.update_session_status(
                db, session_id, "completed", result_summary=result[:500]
            )
            logger.info(f"Planner 평가 완료 (session={session_id})")
        except Exception as e:
            logger.error(f"Planner 평가 실패 (session={session_id}): {e}")
            await queries.update_session_status(
                db, session_id, "failed", result_summary=str(e)
            )
    finally:
        await db.close()


async def scheduled_daily_scan() -> None:
    """매일 정해진 시간에 자동 실행되는 트렌드/연사 스캔."""
    from src.agents.orchestrator import run_daily_scan
    from src.db import queries

    logger.info("일일 자동 스캔 시작")

    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")

    try:
        # 중복 실행 방지: 현재 실행 중인 daily_scan 세션이 있으면 스킵
        cursor = await db.execute(
            """SELECT id FROM research_sessions
               WHERE session_type = 'daily_scan'
               AND status = 'running'""",
        )
        running = await cursor.fetchone()
        if running:
            logger.info("이미 실행 중인 스캔 세션이 있습니다. 스킵합니다.")
            return

        session_id = await queries.create_session(
            db, "daily_scan", "scheduled_daily_scan"
        )

        try:
            result = await run_daily_scan(session_id)
            await queries.update_session_status(
                db, session_id, "completed", result_summary=result
            )
            logger.info(f"일일 자동 스캔 완료 (session={session_id})")
        except Exception as e:
            logger.error(f"일일 자동 스캔 실패 (session={session_id}): {e}")
            logger.error(traceback.format_exc())
            await queries.update_session_status(
                db, session_id, "failed", result_summary=str(e)
            )
    finally:
        await db.close()


def start_scheduler() -> None:
    """스케줄러를 시작합니다."""
    if not settings.daily_scan_enabled:
        logger.info("일일 스캔 비활성화됨 (DAILY_SCAN_ENABLED=false)")
        return

    # 6시간마다 자동 스캔 (00, 06, 12, 18시)
    scheduler.add_job(
        scheduled_daily_scan,
        "interval",
        hours=settings.scan_interval_hours,
        id="periodic_scan",
        replace_existing=True,
    )
    # 기존 일일 스캔도 유지 (메인 스캔 시각)
    scheduler.add_job(
        scheduled_daily_scan,
        "cron",
        hour=settings.daily_scan_hour,
        minute=settings.daily_scan_minute,
        timezone="Asia/Seoul",
        id="daily_scan",
        replace_existing=True,
    )
    # Planner 평가: 일일 스캔 30분 후 실행
    if settings.planner_enabled:
        planner_minute = (settings.daily_scan_minute + 30) % 60
        planner_hour = settings.daily_scan_hour + (
            1 if settings.daily_scan_minute + 30 >= 60 else 0
        )
        scheduler.add_job(
            scheduled_planner_evaluation,
            "cron",
            hour=planner_hour,
            minute=planner_minute,
            timezone="Asia/Seoul",
            id="planner_evaluation",
            replace_existing=True,
        )
    scheduler.start()
    logger.info(
        f"스케줄러 시작 — {settings.scan_interval_hours}시간 간격 + "
        f"매일 {settings.daily_scan_hour:02d}:{settings.daily_scan_minute:02d} KST"
    )


def stop_scheduler() -> None:
    """스케줄러를 중지합니다."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("일일 스캔 스케줄러 중지")
