"""Unit tests for crawler.fetch_job pagination stop conditions."""
from unittest.mock import patch
from model.job import Job
from crawler.fetch_job import fetch_jobs, MAX_STUCK_PAGES


def _job(job_id="1", url="https://www.linkedin.com/jobs/view/1/"):
    return Job(
        id=job_id,
        title="Software Engineer",
        url=url,
        company="Acme",
        location="Tokyo",
    )


def test_fetch_jobs_stops_on_repeated_page_signature():
    repeated = _job(job_id="same-id")
    with patch("crawler.fetch_job.scan_jobs", side_effect=[[repeated], [repeated], [repeated]]) as mock_scan:
        with patch("crawler.fetch_job.is_target_software_role", return_value=False):
            result = fetch_jobs(
                keywords="software%20engineer",
                location="Japan",
                limit_time="r3600",
                country_key="japan",
            )
    assert result == []
    # First page accepted as baseline, second repeated page triggers stop.
    assert mock_scan.call_count == 2


def test_fetch_jobs_stops_after_stuck_pages_when_ids_missing():
    no_id_job = _job(job_id="", url="https://www.linkedin.com/jobs/view/without-id/")
    side_effect_pages = [[no_id_job] for _ in range(MAX_STUCK_PAGES + 2)]
    with patch("crawler.fetch_job.scan_jobs", side_effect=side_effect_pages) as mock_scan:
        result = fetch_jobs(
            keywords="software%20engineer",
            location="Japan",
            limit_time="r3600",
            country_key="japan",
        )
    assert result == []
    assert mock_scan.call_count == MAX_STUCK_PAGES
