"""FastAPI 앱 진입점."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db.database import init_db
from src.api import research, speakers, trends, tracks, feedback, suggestions
from src.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화 + 스케줄러 시작."""
    await init_db()
    start_scheduler()
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
