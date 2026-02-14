"""Unit tests for main.filter_already_seen."""
from conftest import sample_job
from main import filter_already_seen


def test_filter_already_seen_excludes_seen():
    j1 = sample_job(job_id="id-1")
    j2 = sample_job(job_id="id-2")
    jobs = [j1, j2]
    seen = {"id-1"}
    result = filter_already_seen(jobs, seen)
    assert len(result) == 1
    assert result[0].id == "id-2"


def test_filter_already_seen_returns_all_when_none_seen():
    j1 = sample_job(job_id="a")
    j2 = sample_job(job_id="b")
    jobs = [j1, j2]
    seen = set()
    result = filter_already_seen(jobs, seen)
    assert result == jobs


def test_filter_already_seen_returns_empty_when_all_seen():
    j1 = sample_job(job_id="x")
    jobs = [j1]
    seen = {"x"}
    result = filter_already_seen(jobs, seen)
    assert result == []
