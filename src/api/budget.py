"""예산 관리 CRUD API 라우터."""

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite

from src.db.database import get_db
from src.db.models import BudgetItemCreate, BudgetItemUpdate
from src.db import queries

router = APIRouter()


@router.get("")
async def list_budget_items(
    category: str | None = None,
    status: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.list_budget_items(db, category=category, status=status)


@router.get("/summary")
async def budget_summary(
    db: aiosqlite.Connection = Depends(get_db),
):
    return await queries.get_budget_summary(db)


@router.post("", status_code=201)
async def create_budget_item(
    body: BudgetItemCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    item_id = await queries.insert_budget_item(
        db, **body.model_dump(exclude_none=True)
    )
    return {"id": item_id}


@router.patch("/{item_id}")
async def update_budget_item(
    item_id: int,
    body: BudgetItemUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    await queries.update_budget_item(
        db, item_id, **body.model_dump(exclude_none=True)
    )
    return {"ok": True}


@router.delete("/{item_id}")
async def delete_budget_item(
    item_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    deleted = await queries.delete_budget_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget item not found")
    return {"ok": True}
