"""FastAPI 앱 진입점."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db.database import init_db
from src.api import research, speakers, trends, tracks, feedback, suggestions
from src.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


async def _startup_scan() -> None:
    """서버 시작 시 DB가 비어있으면 자동으로 딥 리서치 스캔 실행."""
    import aiosqlite
    from src.db import queries
    from src.agents.orchestrator import run_daily_scan

    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")

    try:
        count = await queries.get_today_suggestion_count(db)
        cursor = await db.execute("SELECT COUNT(*) FROM trends")
        trend_count = (await cursor.fetchone())[0]

        if count == 0 and trend_count == 0:
            logger.info("DB가 비어있습니다. 시작 시 자동 딥 스캔을 실행합니다.")
            session_id = await queries.create_session(
                db, "daily_scan", "startup_auto_scan"
            )
            try:
                result = await run_daily_scan(session_id)
                await queries.update_session_status(
                    db, session_id, "completed", result_summary=result
                )
                logger.info(f"시작 자동 스캔 완료 (session={session_id})")
            except Exception as e:
                logger.error(f"시작 자동 스캔 실패: {e}")
                await queries.update_session_status(
                    db, session_id, "failed", result_summary=str(e)
                )
        else:
            logger.info(f"DB에 이미 데이터 존재 (suggestions={count}, trends={trend_count}). 시작 스캔 스킵.")
    finally:
        await db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화 + 스케줄러 시작 + 자동 스캔."""
    await init_db()
    start_scheduler()
    # 백그라운드에서 자동 스캔 실행 (서버 시작을 블로킹하지 않음)
    asyncio.create_task(_startup_scan())
    yield
    stop_scheduler()


app = FastAPI(
    title="Conference Planning Agent",
    description="AI SUMMIT AND EXPO 2026 기획 에이전트 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(speakers.router, prefix="/api/speakers", tags=["speakers"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["suggestions"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
