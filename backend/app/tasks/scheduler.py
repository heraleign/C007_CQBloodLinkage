"""APScheduler-based task scheduling for lineage platform.

Implements the scheduled jobs from the design document:
  - JOB_001: Lineage ingest sync @ 01:00 daily
  - JOB_002: Log-based lineage parse @ 02:30 daily
  - JOB_003: Neo4j sync @ 04:00 daily
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import async_session_factory

scheduler = AsyncIOScheduler()


async def init_scheduler(app):
    """Register and start all scheduled jobs."""

    async def run_ingest_job():
        async with async_session_factory() as session:
            from app.tasks.ingest_sync import run_ingest_sync

            await run_ingest_sync(session)

    async def run_log_parse_job():
        async with async_session_factory() as session:
            from app.tasks.log_parse_task import run_log_parse

            await run_log_parse(session)

    async def run_neo4j_sync_job():
        from app.services.neo4j_service import Neo4jService

        neo4j = Neo4jService()
        await neo4j.initialize()
        try:
            await neo4j.sync_from_queue()
        finally:
            await neo4j.close()

    scheduler.add_job(
        run_ingest_job,
        CronTrigger(hour=1, minute=0),
        id="job_001_ingest",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        run_log_parse_job,
        CronTrigger(hour=2, minute=30),
        id="job_002_log_parse",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        run_neo4j_sync_job,
        CronTrigger(hour=4, minute=0),
        id="job_003_neo4j_sync",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()


async def stop_scheduler():
    """Gracefully stop the scheduler."""
    scheduler.shutdown(wait=False)
