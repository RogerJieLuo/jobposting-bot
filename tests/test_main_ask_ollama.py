"""Unit tests for main.ask_llm seen-job persistence behavior."""
from unittest.mock import patch
from conftest import sample_job
from main import ask_llm


def test_ask_llm_sends_apply_and_persists_immediately():
    job = sample_job(job_id="id-1", country="us")
    with patch("main.analyze_job", return_value={"answer": "ok", "decision": "apply"}) as mock_analyze:
        with patch("main.send_slack_job") as mock_send:
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_llm([job], provider="ollama", include_company_screening=False)
    mock_analyze.assert_called_once_with(job, provider="ollama", include_company_screening=False)
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-1"]})
    assert out == {"us": ["id-1"]}


def test_ask_llm_sends_skip_and_persists_after_success():
    job = sample_job(job_id="id-2", country="us")
    with patch("main.analyze_jobs", return_value={"id-2": {"answer": "no", "decision": "skip"}}):
        with patch("main.send_slack_job") as mock_send:
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_llm([job], provider="gemini")
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-2"]})
    assert out == {"us": ["id-2"]}


def test_ask_llm_sends_unknown_decision_and_persists_after_success():
    job = sample_job(job_id="id-3", country="us")
    with patch("main.analyze_job", return_value={"answer": "idk", "decision": "maybe"}):
        with patch("main.send_slack_job") as mock_send:
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_llm([job], provider="ollama")
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-3"]})
    assert out == {"us": ["id-3"]}


def test_ask_llm_slack_failure_does_not_persist_seen():
    job = sample_job(job_id="id-4", country="us")
    with patch("main.analyze_job", return_value={"answer": "ok", "decision": "apply"}):
        with patch("main.send_slack_job", side_effect=RuntimeError("slack failed")):
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_llm([job], provider="ollama")
    mock_save.assert_not_called()
    assert out == {}


def test_ask_llm_gemini_uses_batch_analyze():
    job = sample_job(job_id="id-9", country="us")
    with patch("main.analyze_jobs", return_value={"id-9": {"answer": "ok", "decision": "apply"}}) as mock_batch:
        with patch("main.analyze_job") as mock_single:
            with patch("main.send_slack_job"):
                with patch("main.save_seen_jobs"):
                    ask_llm([job], provider="gemini", include_company_screening=True)
    mock_batch.assert_called_once_with([job], provider="gemini", include_company_screening=True)
    mock_single.assert_not_called()
