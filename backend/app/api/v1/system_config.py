"""System configuration API — AI config, system settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, fail, success
from app.models.ai_call_config import AiCallConfig
from app.schemas.ai_config import (
    AiCallConfigCreate,
    AiCallConfigOut,
    AiCallConfigUpdate,
)

router = APIRouter(prefix="/system", tags=["系统配置"])


@router.get("/ai-config", response_model=Result)
async def list_ai_configs(db: AsyncSession = Depends(get_db)):
    """List all AI call configurations."""
    result = await db.execute(
        select(AiCallConfig).order_by(AiCallConfig.create_time)
    )
    configs = result.scalars().all()
    return success(data=[AiCallConfigOut.model_validate(c) for c in configs])


@router.get("/ai-config/{config_id}", response_model=Result)
async def get_ai_config(config_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single AI config by ID."""
    result = await db.execute(
        select(AiCallConfig).where(AiCallConfig.config_id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return fail(code=404, message="配置不存在")
    return success(data=AiCallConfigOut.model_validate(config))


@router.post("/ai-config", response_model=Result)
async def create_ai_config(body: AiCallConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create a new AI call configuration."""
    # Check duplicate
    result = await db.execute(
        select(AiCallConfig).where(AiCallConfig.config_id == body.config_id)
    )
    if result.scalar_one_or_none():
        return fail(code=400, message=f"配置ID '{body.config_id}' 已存在")

    config = AiCallConfig(**body.model_dump())
    db.add(config)
    await db.flush()
    return success(data=AiCallConfigOut.model_validate(config), message="配置创建成功")


@router.put("/ai-config/{config_id}", response_model=Result)
async def update_ai_config(config_id: str, body: AiCallConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing AI call configuration."""
    data = body.model_dump(exclude_none=True)
    if not data:
        return fail(code=400, message="无更新内容")

    result = await db.execute(
        select(AiCallConfig).where(AiCallConfig.config_id == config_id)
    )
    if not result.scalar_one_or_none():
        return fail(code=404, message="配置不存在")

    stmt = update(AiCallConfig).where(AiCallConfig.config_id == config_id).values(**data)
    await db.execute(stmt)
    return success(message="配置更新成功")


@router.delete("/ai-config/{config_id}", response_model=Result)
async def delete_ai_config(config_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an AI call configuration."""
    stmt = delete(AiCallConfig).where(AiCallConfig.config_id == config_id)
    await db.execute(stmt)
    return success(message="配置已删除")
