"""연사 연락 이력 CRUD API 라우터."""

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite

from src.db.database import get_db
from src.db.models import SpeakerContactCreate, SpeakerContactUpdate
from src.db import queries

router = APIRouter()


@router.get("")
async def list_contacts(
    speaker_id: int | None = None,
    status: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_speaker_contacts(
        db, speaker_id=speaker_id, status=status
    )


@router.get("/alerts")
async def follow_up_alerts(
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.get_follow_up_alerts(db)


@router.post("", status_code=201)
async def create_contact(
    body: SpeakerContactCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    contact_id = await queries.insert_speaker_contact(
        db, **body.model_dump(exclude_none=True)
    )
    return {"id": contact_id}


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: int,
    body: SpeakerContactUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    await queries.update_speaker_contact(
        db, contact_id, **body.model_dump(exclude_none=True)
    )
    return {"ok": True}
