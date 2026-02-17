"""Unit tests for crawler.linkedin_parser."""
from crawler.linkedin_parser import parse_job_search_list, _canonical_job_url, _extract_job_id


def test_canonical_job_url_drops_query_and_fragment():
    url = "https://www.linkedin.com/jobs/view/123/?trackingId=abc#x"
    assert _canonical_job_url(url) == "https://www.linkedin.com/jobs/view/123/"


def test_parse_job_search_list_extracts_numeric_id_from_url_when_data_job_id_missing():
    html = """
    <ul>
      <li>
        <a href="https://www.linkedin.com/jobs/view/999/?trackingId=abc"></a>
        <h3>Software Engineer</h3>
        <h4>Acme</h4>
        <span class="job-search-card__location">Remote</span>
      </li>
    </ul>
    """
    jobs = parse_job_search_list(html)
    assert len(jobs) == 1
    assert jobs[0].id == "999"
    assert jobs[0].url == "https://www.linkedin.com/jobs/view/999/"


def test_extract_job_id_supports_slug_path():
    url = "https://www.linkedin.com/jobs/view/software-engineer-ii-1234567890?trackingId=abc"
    assert _extract_job_id(url) == "1234567890"
