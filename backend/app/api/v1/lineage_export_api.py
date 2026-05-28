"""Export API — lineage export (Capability 6)."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import Result, fail, success
from app.schemas.lineage import LineageExportRequest

router = APIRouter(prefix="/export", tags=["血缘导出"])


@router.post("/preview")
async def preview_export(body: LineageExportRequest):
    """Preview export content."""
    return success(
        data={
            "table_count": len(body.table_names),
            "estimated_nodes": 0,
            "estimated_edges": 0,
            "estimated_file_size": "0KB",
        }
    )


@router.post("/execute")
async def execute_export(body: LineageExportRequest, db: AsyncSession = Depends(get_db)):
    """Generate and download lineage export."""
    from app.services.export_service import LineageExportService

    service = LineageExportService(db)
    if body.export_format == "EXCEL":
        file_bytes, filename = await service.export_excel(body)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif body.export_format == "WORD":
        file_bytes, filename = await service.export_word(body)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        return fail(code=400, message="不支持的导出格式")

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
