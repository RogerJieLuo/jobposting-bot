"""Unit tests for utils.seen_jobs with local fallback and Supabase path."""
from unittest.mock import patch, MagicMock

from utils import seen_jobs


def test_save_seen_jobs_local_supports_dict_rows(tmp_path):
    with patch.object(seen_jobs, "SEEN_DIR", tmp_path):
        seen_jobs.save_seen_jobs(
            {
                "us": [
                    {"job_id": "1", "url": "https://linkedin.com/jobs/view/1/", "job_title": "Backend Engineer"},
                    {"job_id": "2", "url": "https://linkedin.com/jobs/view/2/", "job_title": "SWE"},
                ]
            }
        )
        path = tmp_path / "us.txt"
        assert path.exists()
        lines = [x.strip() for x in path.read_text().splitlines() if x.strip()]
        assert "1" in lines
        assert "2" in lines


def test_load_seen_jobs_uses_supabase_when_available():
    with patch.object(
        seen_jobs.seen_jobs_repository,
        "load_seen_jobs",
        return_value={"default": {"u1", "u2"}},
    ):
        out = seen_jobs.load_seen_jobs()

    assert out["default"] == {"u1", "u2"}


def test_load_seen_jobs_falls_back_to_local_when_supabase_unavailable(tmp_path):
    us_file = tmp_path / "us.txt"
    us_file.write_text("id-1\nid-2\n")
    with patch.object(seen_jobs.seen_jobs_repository, "load_seen_jobs", return_value=None):
        with patch.object(seen_jobs, "SEEN_DIR", tmp_path):
            out = seen_jobs.load_seen_jobs()
    assert out["us"] == {"id-1", "id-2"}


def test_get_seen_urls_for_candidates_uses_supabase_incremental_query():
    with patch.object(
        seen_jobs.seen_jobs_repository,
        "find_existing_job_ids",
        return_value={"1", "3"},
    ) as mock_find:
        out = seen_jobs.get_seen_job_ids_for_candidates(["1", "2", "3"])
    assert out == {"1", "3"}
    mock_find.assert_called_once()


def test_get_seen_urls_for_candidates_falls_back_to_local_intersection(tmp_path):
    us_file = tmp_path / "us.txt"
    us_file.write_text("1\n9\n")
    with patch.object(seen_jobs.seen_jobs_repository, "find_existing_job_ids", return_value=None):
        with patch.object(seen_jobs, "SEEN_DIR", tmp_path):
            out = seen_jobs.get_seen_job_ids_for_candidates(["1", "2"])
    assert out == {"1"}
