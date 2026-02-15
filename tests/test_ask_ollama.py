"""Unit tests for Ollama prompt helpers and provider behavior."""
from pathlib import Path
from unittest.mock import patch, MagicMock
from llm.prompt_builder import (
    _prompt_dir,
    _load_prompt_file,
    load_profile,
    load_rules,
    load_company_screening_rules,
    load_prompt_template,
    build_prompt,
)
from llm.parsing import extract_recommendation
from llm.providers.ollama_provider import web_search_company_context
from llm.providers.ollama_provider import analyze as analyze_with_ollama

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_prompt_dir_default():
    assert _prompt_dir(None) == PROJECT_ROOT / "prompts" / "default"
    assert _prompt_dir("default") == PROJECT_ROOT / "prompts" / "default"


def test_prompt_dir_country():
    assert _prompt_dir("canada") == PROJECT_ROOT / "prompts" / "canada"
    assert _prompt_dir("Japan") == PROJECT_ROOT / "prompts" / "japan"


def test_load_profile_default():
    content = load_profile(None)
    assert "Candidate Profile" in content or "backend" in content.lower()


def test_load_rules_default():
    content = load_rules(None)
    assert "Evaluation" in content or "rules" in content.lower()


def test_load_prompt_template_default():
    content = load_prompt_template(None)
    assert "job_description" in content
    assert "candidate_profile" in content
    assert "evaluation_rules" in content


def test_load_company_screening_rules_default():
    content = load_company_screening_rules(None)
    assert "Company Screening Rules" in content


def test_load_prompt_file_fallback_to_default():
    content = _load_prompt_file("profile.txt", "nonexistent_country_xyz")
    assert len(content) > 0


def test_build_prompt_substitutes_all_placeholders():
    job_desc = "Java backend role."
    profile = "Candidate: Java expert."
    rules = "Rule: Prefer backend."
    company_rules = "Company rule: avoid unstable companies."
    company_context = "1. Acme | https://example.com\n   Stable product."
    with patch(
        "llm.prompt_builder._load_prompt_file",
        return_value=(
            "Profile:\n{candidate_profile}\nRules:\n{evaluation_rules}\n"
            "Company:\n{company_name}\nCompanyRules:\n{company_screening_rules}\n"
            "CompanyContext:\n{company_context}\nJob:\n{job_description}"
        ),
    ):
        out = build_prompt(
            job_desc,
            profile,
            rules,
            company_name="Acme",
            company_screening_rules=company_rules,
            company_context=company_context,
            country=None,
            include_company_screening=True,
        )
    assert "Candidate: Java expert." in out
    assert "Rule: Prefer backend." in out
    assert "Acme" in out
    assert "avoid unstable companies" in out
    assert "Stable product." in out
    assert "Java backend role." in out


def test_analyze_with_ollama_returns_structured_response():
    job = MagicMock()
    job.description = "Backend Java role."
    job.url = "https://linkedin.com/jobs/1"
    job.country = "default"
    job.id = "1"
    job.title = "Software Engineer"
    job.company = "Acme"
    job.location = "Toronto"

    with patch("llm.providers.ollama_provider.web_search_company_context", return_value="Company context"):
        with patch("llm.providers.ollama_provider.ollama") as mock_ollama:
            mock_ollama.chat.return_value = {"message": {"content": "Clear recommendation: Apply, match score 80"}}
            result = analyze_with_ollama(job, include_company_screening=True)

    assert result["link"] == "https://linkedin.com/jobs/1"
    assert result["answer"] == "Clear recommendation: Apply, match score 80"
    assert result["decision"] == "apply"
    assert result["provider"] == "ollama"
    mock_ollama.chat.assert_called_once()


def test_extract_recommendation_variants():
    assert extract_recommendation("Clear recommendation: Consider, score 72") == "consider"
    assert extract_recommendation("Recommendation: Skip") == "skip"
    assert extract_recommendation("I would Apply for this role.") == "apply"
    assert extract_recommendation("No clear output") is None


def test_web_search_company_context_formats_results():
    fake_response = {
        "results": [
            {"title": "Acme Company", "link": "https://acme.example", "content": "A stable engineering company."}
        ]
    }
    with patch("llm.providers.ollama_provider.ollama.Client") as mock_client:
        mock_client.return_value.web_search.return_value = fake_response
        out = web_search_company_context("Acme", max_results=1)
    assert "Acme Company" in out
    assert "https://acme.example" in out


def test_web_search_company_context_handles_failure():
    with patch("llm.providers.ollama_provider.ollama.Client") as mock_client:
        mock_client.return_value.web_search.side_effect = ValueError("missing api key")
        out = web_search_company_context("Acme", max_results=1)
    assert "Web search unavailable" in out


def test_analyze_with_ollama_without_company_screening_skips_web_search():
    job = MagicMock()
    job.description = "Backend Java role."
    job.url = "https://linkedin.com/jobs/1"
    job.country = "default"
    job.company = "Acme"

    with patch("llm.providers.ollama_provider.web_search_company_context") as mock_web:
        with patch("llm.providers.ollama_provider.ollama") as mock_ollama:
            mock_ollama.chat.return_value = {"message": {"content": "Clear recommendation: Consider, match score 70"}}
            result = analyze_with_ollama(job, include_company_screening=False)

    mock_web.assert_not_called()
    assert result["decision"] == "consider"
