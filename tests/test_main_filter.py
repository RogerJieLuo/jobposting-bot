"""Unit tests for main.filter_already_seen."""
from conftest import sample_job
from main import filter_already_seen


def test_filter_already_seen_excludes_seen():
    j1 = sample_job(job_id="id-1", country="canada")
    j2 = sample_job(job_id="id-2", country="canada")
    jobs = [j1, j2]
    seen_by_country = {"canada": {"id-1"}}
    result = filter_already_seen(jobs, seen_by_country)
    assert len(result) == 1
    assert result[0].id == "id-2"


def test_filter_already_seen_returns_all_when_none_seen():
    j1 = sample_job(job_id="a", country="us")
    j2 = sample_job(job_id="b", country="us")
    jobs = [j1, j2]
    seen_by_country = {}
    result = filter_already_seen(jobs, seen_by_country)
    assert result == jobs


def test_filter_already_seen_returns_empty_when_all_seen():
    j1 = sample_job(job_id="x", country="japan")
    jobs = [j1]
    seen_by_country = {"japan": {"x"}}
    result = filter_already_seen(jobs, seen_by_country)
    assert result == []
