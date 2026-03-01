"""아젠다/세션 CRUD API 라우터."""

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite

from src.db.database import get_db
from src.db.models import AgendaSessionCreate, AgendaSessionUpdate
from src.db import queries

router = APIRouter()


@router.get("")
async def list_agenda_sessions(
    day: int | None = None,
    track_id: int | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_agenda_sessions(db, day=day, track_id=track_id)


@router.get("/{session_id}")
async def get_agenda_session(
    session_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    session = await queries.get_agenda_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", status_code=201)
async def create_agenda_session(
    body: AgendaSessionCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    session_id = await queries.insert_agenda_session(
        db, **body.model_dump(exclude_none=True)
    )
    return {"id": session_id}


@router.patch("/{session_id}")
async def update_agenda_session(
    session_id: int,
    body: AgendaSessionUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    existing = await queries.get_agenda_session(db, session_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")

    await queries.update_agenda_session(
        db, session_id, **body.model_dump(exclude_none=True)
    )
    return await queries.get_agenda_session(db, session_id)


@router.delete("/{session_id}")
async def delete_agenda_session(
    session_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    deleted = await queries.delete_agenda_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}
