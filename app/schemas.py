from datetime import datetime

from pydantic import BaseModel, Field


class SourceRead(BaseModel):
    id: int
    name: str
    url: str
    source_type: str
    enabled: bool
    last_status: str | None = None
    last_crawled_at: datetime | None = None

    model_config = {"from_attributes": True}


class CrawlRunRead(BaseModel):
    id: int
    source_id: int | None = None
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    jobs_found: int
    jobs_created: int
    jobs_updated: int
    message: str | None = None

    model_config = {"from_attributes": True}


class JobRead(BaseModel):
    id: int
    source_id: int
    company: str
    title: str
    location: str | None = None
    job_type: str | None = None
    season: str | None = None
    apply_url: str | None = None
    source_url: str
    raw_text: str | None = None
    skills_json: str | None = None
    status: str
    is_active: bool
    content_hash: str
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    total: int
    items: list[JobRead]


class UserProfileCreate(BaseModel):
    name: str = "default"
    skills: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    target_directions: list[str] = Field(default_factory=list)
    remote_preference: str | None = None
    blacklist_keywords: list[str] = Field(default_factory=list)


class UserProfileRead(BaseModel):
    id: int
    name: str
    skills: list[str]
    target_locations: list[str]
    target_directions: list[str]
    remote_preference: str | None = None
    blacklist_keywords: list[str]


class MatchRequest(UserProfileCreate):
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=50, ge=1, le=200)


class MatchItem(BaseModel):
    job: JobRead
    score: float
    reasons: list[str]


class MatchResponse(BaseModel):
    items: list[MatchItem]


class HealthResponse(BaseModel):
    status: str
    app: str


class RawJob(BaseModel):
    company: str
    title: str
    location: str | None = None
    job_type: str | None = None
    season: str | None = None
    apply_url: str | None = None
    source_url: str
    raw_text: str


class UserJobUpsert(BaseModel):
    profile_name: str = "default"
    is_favorite: bool = True
    application_status: str = Field(default="saved", pattern="^(saved|interested|applied|interview|offer|rejected|archived)$")
    notes: str | None = None
    applied_at: datetime | None = None


class UserJobRead(BaseModel):
    id: int
    user_id: int
    job_id: int
    is_favorite: bool
    application_status: str
    notes: str | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    job: JobRead

    model_config = {"from_attributes": True}


class TrendPoint(BaseModel):
    label: str
    count: int


class TrendsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    by_job_type: list[TrendPoint]
    by_source: list[TrendPoint]
    by_day_seen: list[TrendPoint]
    top_locations: list[TrendPoint]
    top_skills: list[TrendPoint]
    application_status: list[TrendPoint]
