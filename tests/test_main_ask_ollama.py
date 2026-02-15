"""Unit tests for main.ask_ollama seen-job persistence behavior."""
from unittest.mock import patch
from conftest import sample_job
from main import ask_ollama


def test_ask_ollama_sends_apply_and_persists_immediately():
    job = sample_job(job_id="id-1", country="us")
    with patch("main.analyze_with_ollama", return_value={"ollama_answer": "ok", "decision": "apply"}):
        with patch("main.send_slack_job") as mock_send:
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_ollama([job])
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-1"]})
    assert out == {"us": ["id-1"]}


def test_ask_ollama_sends_skip_and_persists_after_success():
    job = sample_job(job_id="id-2", country="us")
    with patch("main.analyze_with_ollama", return_value={"ollama_answer": "no", "decision": "skip"}):
        with patch("main.send_slack_job") as mock_send:
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_ollama([job])
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-2"]})
    assert out == {"us": ["id-2"]}


def test_ask_ollama_sends_unknown_decision_and_persists_after_success():
    job = sample_job(job_id="id-3", country="us")
    with patch("main.analyze_with_ollama", return_value={"ollama_answer": "idk", "decision": "maybe"}):
        with patch("main.send_slack_job") as mock_send:
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_ollama([job])
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-3"]})
    assert out == {"us": ["id-3"]}


def test_ask_ollama_slack_failure_does_not_persist_seen():
    job = sample_job(job_id="id-4", country="us")
    with patch("main.analyze_with_ollama", return_value={"ollama_answer": "ok", "decision": "apply"}):
        with patch("main.send_slack_job", side_effect=RuntimeError("slack failed")):
            with patch("main.save_seen_jobs") as mock_save:
                out = ask_ollama([job])
    mock_save.assert_not_called()
    assert out == {}
