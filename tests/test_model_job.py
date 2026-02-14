"""Unit tests for model.job.Job."""
from model.job import Job


def test_job_creation():
    j = Job(
        id="1",
        title="Software Engineer",
        url="https://example.com/job/1",
        company="Acme",
        location="Toronto",
    )
    assert j.id == "1"
    assert j.title == "Software Engineer"
    assert j.url == "https://example.com/job/1"
    assert j.company == "Acme"
    assert j.location == "Toronto"
    assert j.country is None
    assert j.description is None


def test_job_with_country():
    j = Job(
        id="2",
        title="Backend Developer",
        url="https://example.com/job/2",
        company="Foo",
        location="Tokyo",
        country="japan",
        description="Java backend.",
    )
    assert j.country == "japan"
    assert j.description == "Java backend."
