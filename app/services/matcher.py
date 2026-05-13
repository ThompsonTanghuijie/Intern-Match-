import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job
from app.schemas import MatchItem, MatchRequest
from app.services.parser import extract_skills


RELATED_SKILLS = {
    "Python": {"FastAPI", "Data Engineering", "Machine Learning", "Airflow", "Spark"},
    "SQL": {"PostgreSQL", "MongoDB", "Data Engineering", "Spark"},
    "Java": {"Spark", "Data Engineering"},
    "C++": {"Machine Learning"},
    "Docker": {"Kubernetes", "AWS"},
    "React": {"TypeScript"},
    "Data Engineering": {"SQL", "Spark", "Airflow", "Python"},
    "Machine Learning": {"Python", "C++"},
}


def _load_skills(job: Job) -> set[str]:
    if job.skills_json:
        try:
            return set(json.loads(job.skills_json))
        except json.JSONDecodeError:
            pass
    return set(extract_skills(f"{job.title} {job.raw_text or ''}"))


def weighted_skill_score(user_skills: set[str], job_skills: set[str]) -> tuple[float, list[str]]:
    if not user_skills:
        return 0.0, []
    exact = user_skills & job_skills
    related_score = 0.0
    related_matches: list[str] = []
    for skill in user_skills - exact:
        related = RELATED_SKILLS.get(skill, set())
        overlap = related & job_skills
        if overlap:
            related_score += 0.5
            related_matches.extend(sorted(overlap))
    denominator = max(len(user_skills), 1)
    score = min((len(exact) + related_score) / denominator, 1.0)
    return score, sorted(exact) + related_matches


def location_score(job_location: str | None, targets: list[str], remote_preference: str | None) -> tuple[float, str | None]:
    text = (job_location or "").lower()
    if remote_preference and remote_preference.lower() in {"remote", "prefer_remote"} and "remote" in text:
        return 1.0, "支持远程"
    if not targets:
        return 0.5, None
    for target in targets:
        if target.lower() in text:
            return 1.0, "地点符合"
    if "remote" in text and remote_preference and remote_preference.lower() != "onsite":
        return 0.8, "远程地点可接受"
    return 0.0, None


def direction_score(title: str, job_type: str | None, directions: list[str]) -> tuple[float, str | None]:
    if not directions:
        return 0.5, None
    text = f"{title} {job_type or ''}".lower()
    for direction in directions:
        if direction.lower() in text:
            return 1.0, "岗位方向匹配"
    aliases = {
        "backend": ["backend", "back end", "software engineer", "platform", "api"],
        "data engineering": ["data engineer", "analytics engineer", "etl", "pipeline"],
        "automation": ["automation", "qa", "test engineer", "sdet"],
        "ai/ml": ["machine learning", "ai", "ml", "model"],
        "new grad": ["new grad", "graduate"],
        "internship": ["intern", "internship"],
    }
    for direction in directions:
        if any(alias in text for alias in aliases.get(direction.lower(), [])):
            return 1.0, "岗位方向匹配"
    return 0.0, None


def freshness_score(last_seen_at: datetime | None) -> tuple[float, str | None]:
    if not last_seen_at:
        return 0.2, None
    now = datetime.now(timezone.utc)
    seen = last_seen_at
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    age_days = max((now - seen).days, 0)
    if age_days <= 3:
        return 1.0, "岗位发布时间较新"
    if age_days <= 14:
        return 0.7, "岗位近期更新"
    if age_days <= 30:
        return 0.4, None
    return 0.1, None


def is_blacklisted(job: Job, keywords: list[str]) -> bool:
    text = f"{job.company} {job.title} {job.location or ''} {job.raw_text or ''}".lower()
    return any(keyword.lower() in text for keyword in keywords if keyword.strip())


def match_jobs(db: Session, request: MatchRequest) -> list[MatchItem]:
    user_skills = {skill.strip() for skill in request.skills if skill.strip()}
    jobs = db.scalars(select(Job).where(Job.is_active.is_(True))).all()
    items: list[MatchItem] = []
    for job in jobs:
        if is_blacklisted(job, request.blacklist_keywords):
            continue
        job_skills = _load_skills(job)
        skill_score, matched_skills = weighted_skill_score(user_skills, job_skills)
        loc_score, loc_reason = location_score(job.location, request.target_locations, request.remote_preference)
        dir_score, dir_reason = direction_score(job.title, job.job_type, request.target_directions)
        fresh_score, fresh_reason = freshness_score(job.last_seen_at)
        score = skill_score * 0.6 + loc_score * 0.15 + dir_score * 0.15 + fresh_score * 0.1
        if score < request.min_score:
            continue
        reasons: list[str] = []
        if matched_skills:
            reasons.append(f"匹配 {', '.join(matched_skills)}")
        elif user_skills:
            reasons.append("核心技能匹配较弱")
        for reason in [loc_reason, dir_reason, fresh_reason]:
            if reason:
                reasons.append(reason)
        items.append(MatchItem(job=job, score=round(score, 4), reasons=reasons))
    return sorted(items, key=lambda item: item.score, reverse=True)[: request.limit]
