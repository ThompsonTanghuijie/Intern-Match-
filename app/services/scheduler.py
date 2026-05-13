import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.crawler_service import run_crawl

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def scheduled_crawl() -> None:
    db = SessionLocal()
    try:
        run_crawl(db)
    finally:
        db.close()


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.scheduler_enabled or scheduler.running:
        return
    scheduler.add_job(
        scheduled_crawl,
        "interval",
        hours=settings.crawl_interval_hours,
        id="crawl_jobs",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("scheduler started, interval=%s hours", settings.crawl_interval_hours)
