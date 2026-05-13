from app.models import Source
from app.schemas import RawJob
from app.services.repository import upsert_job


def seed_job():
    from app.db.session import SessionLocal

    db = SessionLocal()
    source = Source(name="tracking-source", url="https://example.com/readme.md")
    db.add(source)
    db.commit()
    db.refresh(source)
    job, _ = upsert_job(
        db,
        source.id,
        RawJob(
            company="ExampleCloud",
            title="Backend Software Engineer Intern Python FastAPI",
            location="Remote, New York",
            job_type="internship",
            season="2026",
            apply_url="https://example.com/apply",
            source_url="https://example.com/readme.md",
            raw_text="Python FastAPI SQL Docker",
        ),
    )
    db.commit()
    job_id = job.id
    db.close()
    return job_id


def test_tracking_and_trends(client):
    job_id = seed_job()
    response = client.post(
        f"/jobs/{job_id}/tracking",
        json={
            "profile_name": "default",
            "is_favorite": True,
            "application_status": "applied",
            "notes": "Submitted resume",
        },
    )
    assert response.status_code == 200
    assert response.json()["application_status"] == "applied"

    tracked = client.get("/tracking", params={"profile_name": "default"})
    assert tracked.status_code == 200
    assert len(tracked.json()) == 1

    trends = client.get("/analytics/trends")
    assert trends.status_code == 200
    body = trends.json()
    assert body["total_jobs"] == 1
    assert any(item["label"] == "applied" for item in body["application_status"])
