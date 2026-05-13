import json
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, get_db, init_db
from app.models import Job, Source
from app.schemas import (
    CrawlRunRead,
    HealthResponse,
    JobListResponse,
    JobRead,
    MatchRequest,
    MatchResponse,
    SourceRead,
    TrendsResponse,
    UserJobRead,
    UserJobUpsert,
    UserProfileCreate,
    UserProfileRead,
)
from app.services.crawler_service import run_crawl
from app.services.matcher import match_jobs
from app.services.repository import delete_user_job, get_trends, list_user_jobs, query_jobs, save_user_profile, upsert_user_job
from app.services.scheduler import start_scheduler
from app.services.sources import seed_default_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    db = SessionLocal()
    try:
        seed_default_sources(db)
    finally:
        db.close()
    start_scheduler()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name)


@app.post("/crawl/run", response_model=list[CrawlRunRead])
def crawl_run(force: bool = False, db: Session = Depends(get_db)) -> list[CrawlRunRead]:
    return run_crawl(db, force=force)


@app.get("/jobs", response_model=JobListResponse)
def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    q: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    db: Session = Depends(get_db),
) -> JobListResponse:
    total, items = query_jobs(db, skip=skip, limit=limit, q=q, location=location, job_type=job_type)
    return JobListResponse(total=total, items=items)


@app.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/profile", response_model=UserProfileRead)
def save_profile(payload: UserProfileCreate, db: Session = Depends(get_db)) -> UserProfileRead:
    profile = save_user_profile(db, payload)
    return UserProfileRead(
        id=profile.id,
        name=profile.name,
        skills=[item.skill.name for item in profile.skills],
        target_locations=json.loads(profile.target_locations or "[]"),
        target_directions=json.loads(profile.target_directions or "[]"),
        remote_preference=profile.remote_preference,
        blacklist_keywords=json.loads(profile.blacklist_keywords or "[]"),
    )


@app.post("/match", response_model=MatchResponse)
def match(payload: MatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    return MatchResponse(items=match_jobs(db, payload))


@app.post("/jobs/{job_id}/tracking", response_model=UserJobRead)
def save_job_tracking(job_id: int, payload: UserJobUpsert, db: Session = Depends(get_db)) -> UserJobRead:
    try:
        return upsert_user_job(db, job_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/tracking", response_model=list[UserJobRead])
def get_tracking(
    profile_name: str = "default",
    status: str | None = None,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
) -> list:
    return list_user_jobs(db, profile_name=profile_name, status=status, favorites_only=favorites_only)


@app.delete("/tracking/{tracking_id}")
def remove_tracking(tracking_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    deleted = delete_user_job(db, tracking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    return {"deleted": True}


@app.get("/analytics/trends", response_model=TrendsResponse)
def analytics_trends(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)) -> TrendsResponse:
    return get_trends(db, limit=limit)


@app.get("/sources", response_model=list[SourceRead])
def get_sources(db: Session = Depends(get_db)) -> list[Source]:
    seed_default_sources(db)
    return db.scalars(select(Source).order_by(Source.name)).all()
