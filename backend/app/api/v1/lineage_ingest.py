"""Ingestion API — data ingestion lineage sync (Capability 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, success

router = APIRouter(prefix="/ingest", tags=["入湖血缘"])


@router.post("/sync", response_model=Result)
async def trigger_ingest_sync(db: AsyncSession = Depends(get_db)):
    """Manually trigger ingest lineage sync."""
    from app.tasks.ingest_sync import run_ingest_sync
    await run_ingest_sync(db)
    return success(message="入湖血缘同步任务已触发")


@router.get("/status", response_model=Result)
async def get_ingest_status(db: AsyncSession = Depends(get_db)):
    """Get latest ingest sync status."""
    from app.models.script_parse_result import ScriptParseResult
    from sqlalchemy import select, func

    stmt = select(func.count()).select_from(ScriptParseResult)
    result = await db.execute(stmt)
    count = result.scalar()
    return success(data={"total_syncs": count})
