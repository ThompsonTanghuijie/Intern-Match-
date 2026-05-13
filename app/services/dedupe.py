import hashlib
import re

from app.schemas import RawJob


def normalize_key_part(value: str | None) -> str:
    normalized = (value or "").lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^\w\s:/.-]", "", normalized)
    return normalized


def job_unique_key(job: RawJob) -> str:
    url_part = job.apply_url or job.source_url
    parts = [job.company, job.title, job.location or "", url_part]
    return "|".join(normalize_key_part(part) for part in parts)


def content_hash_for_job(job: RawJob) -> str:
    return hashlib.sha256(job_unique_key(job).encode("utf-8")).hexdigest()
