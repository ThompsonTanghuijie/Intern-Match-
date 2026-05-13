import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawlers.github_markdown import GitHubMarkdownCrawler
from app.models import CrawlRun, Source
from app.services.repository import upsert_job
from app.services.sources import seed_default_sources

logger = logging.getLogger(__name__)


def run_crawl(db: Session, force: bool = False) -> list[CrawlRun]:
    seed_default_sources(db)
    sources = db.scalars(select(Source).where(Source.enabled.is_(True))).all()
    crawler = GitHubMarkdownCrawler()
    runs: list[CrawlRun] = []
    for source in sources:
        run = CrawlRun(source_id=source.id, status="running")
        db.add(run)
        db.commit()
        db.refresh(run)
        try:
            if force:
                source.etag = None
                source.last_modified = None
            fetched, raw_jobs = crawler.crawl(source)
            created = 0
            updated = 0
            for raw_job in raw_jobs:
                _, was_created = upsert_job(db, source.id, raw_job)
                created += 1 if was_created else 0
                updated += 0 if was_created else 1
            source.etag = fetched.etag or source.etag
            source.last_modified = fetched.last_modified or source.last_modified
            source.last_status = "not_modified" if fetched.not_modified else "ok"
            source.last_crawled_at = datetime.utcnow()
            run.status = "success"
            run.jobs_found = len(raw_jobs)
            run.jobs_created = created
            run.jobs_updated = updated
            run.finished_at = datetime.utcnow()
            run.message = "No changes" if fetched.not_modified else None
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("crawl failed for %s", source.name)
            source = db.get(Source, source.id)
            run = db.get(CrawlRun, run.id)
            source.last_status = "failed"
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.message = str(exc)
            db.commit()
        db.refresh(run)
        runs.append(run)
    return runs
