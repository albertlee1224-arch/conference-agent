"""연사 CRUD API 라우터."""

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite

from src.db.database import get_db
from src.db.models import SpeakerCreate, SpeakerUpdate, Speaker
from src.db import queries

router = APIRouter()


@router.get("")
async def list_speakers(
    status: str | None = None,
    tier: str | None = None,
    track_id: int | None = None,
    sort: str = "overall_score",
    limit: int = 50,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_speakers(
        db, status=status, tier=tier, track_id=track_id,
        sort_by=sort, limit=limit,
    )


@router.get("/{speaker_id}")
async def get_speaker(
    speaker_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    speaker = await queries.get_speaker(db, speaker_id)
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return speaker


@router.post("", status_code=201)
async def create_speaker(
    body: SpeakerCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    speaker_id = await queries.insert_speaker(db, **body.model_dump(exclude_none=True))
    return {"id": speaker_id}


@router.patch("/{speaker_id}")
async def update_speaker(
    speaker_id: int,
    body: SpeakerUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    existing = await queries.get_speaker(db, speaker_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Speaker not found")

    await queries.update_speaker(db, speaker_id, **body.model_dump(exclude_none=True))
    return await queries.get_speaker(db, speaker_id)


@router.delete("/{speaker_id}")
async def delete_speaker(
    speaker_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    deleted = await queries.delete_speaker(db, speaker_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return {"ok": True}
