"""트렌드 API 라우터."""

from fastapi import APIRouter, Depends

import aiosqlite

from src.db.database import get_db
from src.db.models import TrendCreate
from src.db import queries

router = APIRouter()


@router.get("")
async def list_trends(
    category: str | None = None,
    min_relevance: float | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_trends(db, category=category, min_relevance=min_relevance)


@router.get("/{trend_id}")
async def get_trend(
    trend_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    trend = await queries.get_trend(db, trend_id)
    if not trend:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trend not found")
    return trend
