"""Pytest configuration and shared fixtures."""
from pathlib import Path
import sys

# Add project root so imports like "from model.job import Job" work when running pytest
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def sample_job(
    job_id="job-1",
    title="Software Engineer",
    url="https://linkedin.com/jobs/1",
    company="Acme Inc",
    location="Toronto, Canada",
    country="canada",
    description="Backend role with Java.",
):
    """Create a Job instance for tests (avoids importing Job in conftest before path is set)."""
    from model.job import Job
    j = Job(
        id=job_id,
        title=title,
        url=url,
        company=company,
        location=location,
        country=country,
        description=description,
    )
    return j


def sample_slack_variables():
    return {
        "title": "Software Engineer",
        "company": "Acme Inc",
        "location": "Toronto, Canada",
        "summary": "Strong match. Apply.",
        "link": "https://linkedin.com/jobs/1",
    }
