from app.models import Source
from app.schemas import MatchRequest, RawJob
from app.services.matcher import match_jobs
from app.services.repository import upsert_job


def test_match_jobs_explains_reasons(reset_db):
    from app.db.session import SessionLocal

    db = SessionLocal()
    source = Source(name="sample", url="https://example.com/readme.md")
    db.add(source)
    db.commit()
    db.refresh(source)
    upsert_job(
        db,
        source.id,
        RawJob(
            company="DataWorks",
            title="Data Engineering Intern",
            location="Remote",
            job_type="internship",
            season="2026",
            apply_url="https://example.com/apply",
            source_url="https://example.com/readme.md",
            raw_text="Python SQL Spark Airflow Data Engineering",
        ),
    )
    db.commit()
    result = match_jobs(
        db,
        MatchRequest(
            skills=["Python", "SQL"],
            target_locations=["Remote"],
            target_directions=["data engineering"],
            remote_preference="prefer_remote",
            min_score=0.1,
        ),
    )
    assert result
    assert result[0].score > 0.7
    assert any("匹配" in reason for reason in result[0].reasons)
    db.close()
