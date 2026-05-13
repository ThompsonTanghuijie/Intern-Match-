from app.services.dedupe import content_hash_for_job
from app.services.parser import extract_skills, parse_github_markdown_jobs


def test_parse_markdown_jobs():
    markdown = """
| Company | Role | Location | Application |
| --- | --- | --- | --- |
| DataWorks | Data Engineering Intern Python SQL | Remote | [Apply](https://example.com/apply) |
"""
    jobs = parse_github_markdown_jobs(markdown, "https://raw.example/readme.md")
    assert len(jobs) == 1
    assert jobs[0].company == "DataWorks"
    assert jobs[0].apply_url == "https://example.com/apply"
    assert jobs[0].job_type == "internship"


def test_extract_skills():
    skills = extract_skills("Backend role using Python, FastAPI, PostgreSQL and Docker")
    assert {"Python", "FastAPI", "PostgreSQL", "Docker"}.issubset(set(skills))


def test_content_hash_is_stable():
    job = parse_github_markdown_jobs(
        """
| Company | Role | Location | Application |
| --- | --- | --- | --- |
| A | Backend Intern | Remote | [Apply](https://a.test) |
""",
        "https://source.test",
    )[0]
    assert content_hash_for_job(job) == content_hash_for_job(job)
