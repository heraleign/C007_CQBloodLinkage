"""Unified API response helpers."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None


def success(data: Any = None, message: str = "success") -> Result:
    return Result(code=200, message=message, data=data)


def fail(code: int = 400, message: str = "error", data: Any = None) -> Result:
    return Result(code=code, message=message, data=data)
