import json
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Company, Job, JobSkill, Skill, Source, UserJob, UserProfile, UserSkill
from app.schemas import RawJob, TrendPoint, TrendsResponse, UserJobUpsert, UserProfileCreate
from app.services.dedupe import content_hash_for_job
from app.services.parser import extract_skills


def get_or_create_skill(db: Session, name: str) -> Skill:
    skill = db.scalar(select(Skill).where(Skill.name == name))
    if skill:
        return skill
    skill = Skill(name=name)
    db.add(skill)
    db.flush()
    return skill


def ensure_company(db: Session, name: str) -> None:
    if not db.scalar(select(Company).where(Company.name == name)):
        db.add(Company(name=name))


def upsert_job(db: Session, source_id: int, raw_job: RawJob) -> tuple[Job, bool]:
    content_hash = content_hash_for_job(raw_job)
    now = datetime.utcnow()
    skills = extract_skills(f"{raw_job.title} {raw_job.raw_text}")
    job = db.scalar(select(Job).where(Job.content_hash == content_hash))
    created = False
    if job is None:
        job = Job(
            source_id=source_id,
            company=raw_job.company,
            title=raw_job.title,
            location=raw_job.location,
            job_type=raw_job.job_type,
            season=raw_job.season,
            apply_url=raw_job.apply_url,
            source_url=raw_job.source_url,
            raw_text=raw_job.raw_text,
            skills_json=json.dumps(skills, ensure_ascii=False),
            content_hash=content_hash,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(job)
        db.flush()
        created = True
    else:
        job.last_seen_at = now
        job.is_active = True
        job.status = "open"
        job.raw_text = raw_job.raw_text
        job.skills_json = json.dumps(skills, ensure_ascii=False)
    ensure_company(db, raw_job.company)
    job.skills.clear()
    for skill_name in skills:
        skill = get_or_create_skill(db, skill_name)
        job.skills.append(JobSkill(skill=skill, weight=1.0))
    return job, created


def query_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    q: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
) -> tuple[int, list[Job]]:
    statement = select(Job).where(Job.is_active.is_(True))
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(Job.company.ilike(like), Job.title.ilike(like), Job.raw_text.ilike(like)))
    if location:
        statement = statement.where(Job.location.ilike(f"%{location}%"))
    if job_type:
        statement = statement.where(Job.job_type == job_type)
    total = len(db.scalars(statement).all())
    items = db.scalars(statement.order_by(Job.last_seen_at.desc()).offset(skip).limit(limit)).all()
    return total, items


def save_user_profile(db: Session, payload: UserProfileCreate) -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.name == payload.name))
    if profile is None:
        profile = UserProfile(name=payload.name)
        db.add(profile)
        db.flush()
    profile.target_locations = json.dumps(payload.target_locations, ensure_ascii=False)
    profile.target_directions = json.dumps(payload.target_directions, ensure_ascii=False)
    profile.remote_preference = payload.remote_preference
    profile.blacklist_keywords = json.dumps(payload.blacklist_keywords, ensure_ascii=False)
    profile.skills.clear()
    for skill_name in payload.skills:
        clean = skill_name.strip()
        if clean:
            profile.skills.append(UserSkill(skill=get_or_create_skill(db, clean), weight=1.0))
    db.commit()
    db.refresh(profile)
    return profile


def get_or_create_profile(db: Session, name: str = "default") -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.name == name))
    if profile:
        return profile
    profile = UserProfile(name=name)
    db.add(profile)
    db.flush()
    return profile


def upsert_user_job(db: Session, job_id: int, payload: UserJobUpsert) -> UserJob:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    profile = get_or_create_profile(db, payload.profile_name)
    tracked = db.scalar(select(UserJob).where(UserJob.user_id == profile.id, UserJob.job_id == job_id))
    if tracked is None:
        tracked = UserJob(user_id=profile.id, job_id=job_id)
        db.add(tracked)
        db.flush()
    tracked.is_favorite = payload.is_favorite
    tracked.application_status = payload.application_status
    tracked.notes = payload.notes
    tracked.applied_at = payload.applied_at
    db.commit()
    db.refresh(tracked)
    return tracked


def list_user_jobs(
    db: Session,
    profile_name: str = "default",
    status: str | None = None,
    favorites_only: bool = False,
) -> list[UserJob]:
    statement = select(UserJob).join(UserProfile).where(UserProfile.name == profile_name)
    if status:
        statement = statement.where(UserJob.application_status == status)
    if favorites_only:
        statement = statement.where(UserJob.is_favorite.is_(True))
    return db.scalars(statement.order_by(UserJob.updated_at.desc())).all()


def delete_user_job(db: Session, tracking_id: int) -> bool:
    tracked = db.get(UserJob, tracking_id)
    if not tracked:
        return False
    db.delete(tracked)
    db.commit()
    return True


def _trend_rows(rows: list[tuple[str | None, int]]) -> list[TrendPoint]:
    return [TrendPoint(label=label or "unknown", count=count) for label, count in rows]


def get_trends(db: Session, limit: int = 10) -> TrendsResponse:
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    active_jobs = db.scalar(select(func.count(Job.id)).where(Job.is_active.is_(True))) or 0

    by_job_type = db.execute(
        select(Job.job_type, func.count(Job.id)).group_by(Job.job_type).order_by(func.count(Job.id).desc())
    ).all()
    by_source = db.execute(
        select(Source.name, func.count(Job.id))
        .join(Job, Job.source_id == Source.id)
        .group_by(Source.name)
        .order_by(func.count(Job.id).desc())
    ).all()
    by_day_seen = db.execute(
        select(func.date(Job.first_seen_at), func.count(Job.id))
        .group_by(func.date(Job.first_seen_at))
        .order_by(func.date(Job.first_seen_at).desc())
        .limit(14)
    ).all()
    top_skills = db.execute(
        select(Skill.name, func.count(JobSkill.job_id))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .group_by(Skill.name)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(limit)
    ).all()
    application_status = db.execute(
        select(UserJob.application_status, func.count(UserJob.id))
        .group_by(UserJob.application_status)
        .order_by(func.count(UserJob.id).desc())
    ).all()

    locations: dict[str, int] = {}
    for location in db.scalars(select(Job.location).where(Job.location.is_not(None))).all():
        for part in str(location).replace("/", ",").replace("|", ",").split(","):
            clean = part.strip()
            if clean:
                locations[clean] = locations.get(clean, 0) + 1
    top_locations = sorted(locations.items(), key=lambda item: item[1], reverse=True)[:limit]

    return TrendsResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        by_job_type=_trend_rows(by_job_type),
        by_source=_trend_rows(by_source),
        by_day_seen=_trend_rows(list(reversed(by_day_seen))),
        top_locations=_trend_rows(top_locations),
        top_skills=_trend_rows(top_skills),
        application_status=_trend_rows(application_status),
    )
