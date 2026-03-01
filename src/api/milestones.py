"""마일스톤/타임라인 CRUD API 라우터."""

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite

from src.db.database import get_db
from src.db.models import MilestoneCreate, MilestoneUpdate
from src.db import queries

router = APIRouter()


@router.get("")
async def list_milestones(
    phase: str | None = None,
    status: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_milestones(db, phase=phase, status=status)


@router.post("", status_code=201)
async def create_milestone(
    body: MilestoneCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    milestone_id = await queries.insert_milestone(
        db, **body.model_dump(exclude_none=True)
    )
    return {"id": milestone_id}


@router.patch("/{milestone_id}")
async def update_milestone(
    milestone_id: int,
    body: MilestoneUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    await queries.update_milestone(
        db, milestone_id, **body.model_dump(exclude_none=True)
    )
    return {"ok": True}


@router.delete("/{milestone_id}")
async def delete_milestone(
    milestone_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    deleted = await queries.delete_milestone(db, milestone_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return {"ok": True}
