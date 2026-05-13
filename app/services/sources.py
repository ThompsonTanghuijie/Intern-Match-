from sqlalchemy.orm import Session

from app.models import Source


DEFAULT_SOURCES = [
    {
        "name": "SimplifyJobs Summer 2026 Tech Internships",
        "url": "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md",
    },
    {
        "name": "SimplifyJobs New Grad Positions",
        "url": "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md",
    },
    {
        "name": "speedyapply 2026 SWE College Jobs",
        "url": "https://raw.githubusercontent.com/speedyapply/2026-SWE-College-Jobs/main/README.md",
    },
    {
        "name": "jobright-ai 2026 Internship New Grad",
        "url": "https://raw.githubusercontent.com/jobright-ai/2026-Internship-New-Grad/main/README.md",
    },
]


def seed_default_sources(db: Session) -> None:
    existing = {source.name for source in db.query(Source).all()}
    for item in DEFAULT_SOURCES:
        if item["name"] not in existing:
            db.add(Source(name=item["name"], url=item["url"], source_type="github_markdown"))
    db.commit()
