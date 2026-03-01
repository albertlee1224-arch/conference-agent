"""트랙 CRUD API 라우터."""

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite

from src.db.database import get_db
from src.db.models import TrackCreate, TrackUpdate
from src.db import queries

router = APIRouter()


@router.get("")
async def list_tracks(
    db: aiosqlite.Connection = Depends(get_db),
):
    tracks = await queries.list_tracks(db)
    # 각 트랙에 연결된 트렌드도 포함
    for track in tracks:
        track["trends"] = await queries.get_track_trends(db, track["id"])
    return tracks


@router.get("/{track_id}")
async def get_track(
    track_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    track = await queries.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    track["trends"] = await queries.get_track_trends(db, track_id)
    return track


@router.post("", status_code=201)
async def create_track(
    body: TrackCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    track_id = await queries.insert_track(db, **body.model_dump(exclude_none=True))
    return {"id": track_id}


@router.patch("/{track_id}")
async def update_track(
    track_id: int,
    body: TrackUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    existing = await queries.get_track(db, track_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Track not found")

    update_data = body.model_dump(exclude_none=True)
    trend_ids = update_data.pop("trend_ids", None)

    if update_data:
        await queries.update_track(db, track_id, **update_data)

    if trend_ids is not None:
        await queries.set_track_trends(db, track_id, trend_ids)

    track = await queries.get_track(db, track_id)
    track["trends"] = await queries.get_track_trends(db, track_id)
    return track
