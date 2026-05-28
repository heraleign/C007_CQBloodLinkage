"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    atom_services,
    lineage_analysis,
    lineage_edges,
    lineage_export_api,
    lineage_ingest,
    lineage_nodes,
    system_config,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.tasks.scheduler import init_scheduler
    await init_scheduler(app)
    yield
    # Shutdown
    from app.tasks.scheduler import stop_scheduler
    await stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(lineage_nodes.router, prefix="/api/v1")
app.include_router(lineage_edges.router, prefix="/api/v1")
app.include_router(lineage_analysis.router, prefix="/api/v1")
app.include_router(lineage_ingest.router, prefix="/api/v1")
app.include_router(lineage_export_api.router, prefix="/api/v1")
app.include_router(atom_services.router, prefix="/api/v1")
app.include_router(system_config.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
