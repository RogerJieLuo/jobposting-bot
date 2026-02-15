"""Unit tests for Gemini provider using google genai SDK."""
from unittest.mock import patch, MagicMock
from model.job import Job

from llm.providers.gemini_provider import analyze, analyze_batch, _parse_batch_response


def test_analyze_with_gemini_returns_structured_response():
    job = MagicMock()
    job.description = "Backend Java role."
    job.url = "https://linkedin.com/jobs/1"
    job.country = "default"
    job.company = "Acme"

    fake_result = MagicMock()
    fake_result.text = "Clear recommendation: Apply, match score 81"

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_result

    with patch("llm.providers.gemini_provider.load_gemini_api_key", return_value="fake-key"):
        with patch("llm.providers.gemini_provider.genai.Client", return_value=fake_client) as mock_client:
            out = analyze(job, include_company_screening=True)

    assert out["provider"] == "gemini"
    assert out["decision"] == "apply"
    assert "Apply" in out["answer"]
    mock_client.assert_called_once_with(api_key="fake-key")
    fake_client.models.generate_content.assert_called_once()


def test_analyze_with_gemini_requires_api_key():
    job = MagicMock()
    job.description = "Backend Java role."
    job.url = "https://linkedin.com/jobs/1"
    job.country = "default"
    job.company = "Acme"

    with patch("llm.providers.gemini_provider.load_gemini_api_key", return_value=""):
        try:
            analyze(job, include_company_screening=False)
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "gemini_api_key.txt" in str(e)


def test_parse_batch_response_json_fence():
    text = """```json
{"jobs":[{"job_id":"a1","recommendation":"Apply","summary":"good"}]}
```"""
    items = _parse_batch_response(text)
    assert len(items) == 1
    assert items[0]["job_id"] == "a1"


def test_analyze_batch_with_gemini_maps_results_by_job_id():
    jobs = [
        Job(id="j1", title="Backend Engineer", url="https://x/j1", company="Acme", location="Vancouver", country="default", description="d1"),
        Job(id="j2", title="SWE", url="https://x/j2", company="Beta", location="Tokyo", country="default", description="d2"),
    ]
    fake_result = MagicMock()
    fake_result.text = '{"jobs":[{"job_id":"j1","recommendation":"Apply","summary":"fit"},{"job_id":"j2","recommendation":"Skip","summary":"not fit"}]}'
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_result

    with patch("llm.providers.gemini_provider.load_gemini_api_key", return_value="fake-key"):
        with patch("llm.providers.gemini_provider.genai.Client", return_value=fake_client):
            out = analyze_batch(jobs, include_company_screening=False)

    assert out["j1"]["decision"] == "apply"
    assert out["j2"]["decision"] == "skip"


def test_analyze_batch_splits_when_batch_limit_exceeded():
    jobs = [
        Job(
            id=f"j{i}",
            title="Backend Engineer",
            url=f"https://x/j{i}",
            company="Acme",
            location="Vancouver",
            country="default",
            description="desc",
        )
        for i in range(1, 4)
    ]
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [
        MagicMock(text='{"jobs":[{"job_id":"j1","recommendation":"Apply","summary":"ok"},{"job_id":"j2","recommendation":"Consider","summary":"ok"}]}'),
        MagicMock(text='{"jobs":[{"job_id":"j3","recommendation":"Skip","summary":"ok"}]}'),
    ]

    with patch("llm.providers.gemini_provider.load_gemini_api_key", return_value="fake-key"):
        with patch("llm.providers.gemini_provider.genai.Client", return_value=fake_client):
            with patch("llm.providers.gemini_provider.MAX_BATCH_JOBS", 2):
                out = analyze_batch(jobs, include_company_screening=False)

    assert fake_client.models.generate_content.call_count == 2
    assert out["j1"]["decision"] == "apply"
    assert out["j2"]["decision"] == "consider"
    assert out["j3"]["decision"] == "skip"
