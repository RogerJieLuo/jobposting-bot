"""Unit tests for llm.service provider routing."""
from unittest.mock import patch, MagicMock
import pytest

from llm.service import analyze_job, analyze_jobs, normalize_provider


def test_normalize_provider_accepts_known_values():
    assert normalize_provider("ollama") == "ollama"
    assert normalize_provider("GEMINI") == "gemini"


def test_normalize_provider_rejects_unknown():
    with pytest.raises(ValueError):
        normalize_provider("unknown")


def test_analyze_job_routes_to_ollama():
    job = MagicMock()
    with patch("llm.service.analyze_with_ollama", return_value={"answer": "ok"}) as mock_ollama:
        out = analyze_job(job, provider="ollama", include_company_screening=False)
    mock_ollama.assert_called_once_with(job, include_company_screening=False)
    assert out["answer"] == "ok"


def test_analyze_job_routes_to_gemini():
    job = MagicMock()
    with patch("llm.service.analyze_with_gemini", return_value={"answer": "ok"}) as mock_gemini:
        out = analyze_job(job, provider="gemini", include_company_screening=True)
    mock_gemini.assert_called_once_with(job, include_company_screening=True)
    assert out["answer"] == "ok"


def test_analyze_jobs_routes_to_gemini_batch():
    job = MagicMock()
    with patch("llm.service.analyze_batch_with_gemini", return_value={"id-1": {"answer": "ok"}}) as mock_batch:
        out = analyze_jobs([job], provider="gemini", include_company_screening=False)
    mock_batch.assert_called_once_with([job], include_company_screening=False)
    assert "id-1" in out


def test_analyze_jobs_routes_to_ollama_per_job():
    job = MagicMock()
    job.id = "id-1"
    with patch("llm.service.analyze_with_ollama", return_value={"answer": "ok"}) as mock_ollama:
        out = analyze_jobs([job], provider="ollama", include_company_screening=True)
    mock_ollama.assert_called_once_with(job, include_company_screening=True)
    assert out["id-1"]["answer"] == "ok"
