"""Pydantic schemas for AI call configuration."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AiCallConfigCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    config_id: str
    ai_capability: str  # SQL_EXTRACT / LINEAGE_PARSE
    model_name: str
    api_endpoint: str
    api_key: str = ""
    max_tokens: int = 4096
    temperature: Decimal = Decimal("0.1")
    timeout_ms: int = 30000
    retry_count: int = 2
    enabled: int = 1


class AiCallConfigUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[Decimal] = None
    timeout_ms: Optional[int] = None
    retry_count: Optional[int] = None
    enabled: Optional[int] = None


class AiCallConfigOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    config_id: str
    ai_capability: str
    model_name: str
    api_endpoint: str
    api_key: str = ""
    max_tokens: int = 4096
    temperature: Decimal = Decimal("0.1")
    timeout_ms: int = 30000
    retry_count: int = 2
    enabled: int = 1
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
