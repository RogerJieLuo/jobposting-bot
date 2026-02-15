"""Unit tests for llm.ask_ollama (prompt building and file loading; no Ollama API calls)."""
from pathlib import Path
from unittest.mock import patch, MagicMock
from llm.ask_ollama import (
    _prompt_dir,
    _load_prompt_file,
    load_profile,
    load_rules,
    load_prompt_template,
    build_prompt,
    analyze_with_ollama,
    extract_recommendation,
)

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


def test_load_prompt_file_fallback_to_default():
    # When country dir does not exist, should use default
    content = _load_prompt_file("profile.txt", "nonexistent_country_xyz")
    assert len(content) > 0


def test_build_prompt_substitutes_all_placeholders():
    job_desc = "Java backend role."
    profile = "Candidate: Java expert."
    rules = "Rule: Prefer backend."
    with patch("llm.ask_ollama.load_prompt_template", return_value=(
        "Profile:\n{candidate_profile}\nRules:\n{evaluation_rules}\nJob:\n{job_description}"
    )):
        out = build_prompt(job_desc, profile, rules, country=None)
    assert "Candidate: Java expert." in out
    assert "Rule: Prefer backend." in out
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

    with patch("llm.ask_ollama.ollama") as mock_ollama:
        mock_ollama.chat.return_value = {"message": {"content": "Clear recommendation: Apply, match score 80"}}
        result = analyze_with_ollama(job)

    assert result["link"] == "https://linkedin.com/jobs/1"
    assert result["ollama_answer"] == "Clear recommendation: Apply, match score 80"
    assert result["decision"] == "apply"
    mock_ollama.chat.assert_called_once()


def test_extract_recommendation_variants():
    assert extract_recommendation("Clear recommendation: Consider, score 72") == "consider"
    assert extract_recommendation("Recommendation: Skip") == "skip"
    assert extract_recommendation("I would Apply for this role.") == "apply"
    assert extract_recommendation("No clear output") is None
