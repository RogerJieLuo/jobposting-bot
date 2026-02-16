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


def test_ask_llm_gemini_failure_falls_back_to_ollama_when_enabled():
    job = sample_job(job_id="id-10", country="us")
    with patch("main.allow_ollama_fallback", True):
        with patch("main.analyze_jobs", side_effect=RuntimeError("gemini down")):
            with patch("main.analyze_job", return_value={"answer": "fallback", "decision": "apply"}) as mock_single:
                with patch("main.send_slack_job") as mock_send:
                    with patch("main.save_seen_jobs") as mock_save:
                        out = ask_llm([job], provider="gemini", include_company_screening=False)
    mock_single.assert_called_once_with(job, provider="ollama", include_company_screening=False)
    mock_send.assert_called_once()
    mock_save.assert_called_once_with({"us": ["id-10"]})
    assert out == {"us": ["id-10"]}


def test_ask_llm_gemini_failure_does_not_fall_back_when_disabled():
    job = sample_job(job_id="id-11", country="us")
    with patch("main.allow_ollama_fallback", False):
        with patch("main.analyze_jobs", side_effect=RuntimeError("gemini down")):
            with patch("main.analyze_job") as mock_single:
                with patch("main.send_slack_job") as mock_send:
                    with patch("main.save_seen_jobs") as mock_save:
                        out = ask_llm([job], provider="gemini", include_company_screening=False)
    mock_single.assert_not_called()
    mock_send.assert_not_called()
    mock_save.assert_not_called()
    assert out == {}


def test_ask_llm_gemini_partial_failure_falls_back_only_failed_jobs():
    us_job = sample_job(job_id="id-20", country="us")
    ca_job = sample_job(job_id="id-21", country="canada")

    def _analyze_jobs_side_effect(jobs, provider, include_company_screening):
        if jobs[0].country == "us":
            return {"id-20": {"answer": "gemini-ok", "decision": "apply"}}
        raise RuntimeError("gemini failed for canada")

    with patch("main.allow_ollama_fallback", True):
        with patch("main.analyze_jobs", side_effect=_analyze_jobs_side_effect):
            with patch("main.analyze_job", return_value={"answer": "ollama-fallback", "decision": "apply"}) as mock_single:
                with patch("main.send_slack_job") as mock_send:
                    with patch("main.save_seen_jobs") as mock_save:
                        out = ask_llm([us_job, ca_job], provider="gemini", include_company_screening=False)

    mock_single.assert_called_once_with(ca_job, provider="ollama", include_company_screening=False)
    assert mock_send.call_count == 2
    assert mock_save.call_count == 2
    assert out == {"us": ["id-20"], "canada": ["id-21"]}


def test_ask_llm_gemini_failure_stops_remaining_countries_and_fallbacks_all_remaining():
    us_job = sample_job(job_id="id-30", country="us")
    ca_job = sample_job(job_id="id-31", country="canada")
    jp_job = sample_job(job_id="id-32", country="japan")

    def _analyze_jobs_side_effect(jobs, provider, include_company_screening):
        if jobs[0].country == "us":
            return {"id-30": {"answer": "gemini-ok", "decision": "apply"}}
        if jobs[0].country == "canada":
            raise RuntimeError("gemini failed for canada")
        raise AssertionError("Gemini should not be called for countries after first failure")

    with patch("main.allow_ollama_fallback", True):
        with patch("main.analyze_jobs", side_effect=_analyze_jobs_side_effect) as mock_batch:
            with patch("main.analyze_job", return_value={"answer": "ollama-fallback", "decision": "apply"}) as mock_single:
                with patch("main.send_slack_job") as mock_send:
                    with patch("main.save_seen_jobs") as mock_save:
                        out = ask_llm([us_job, ca_job, jp_job], provider="gemini", include_company_screening=False)

    assert mock_batch.call_count == 2
    assert mock_single.call_count == 2
    fallback_jobs = [call.args[0] for call in mock_single.call_args_list]
    assert ca_job in fallback_jobs
    assert jp_job in fallback_jobs
    assert mock_send.call_count == 3
    assert mock_save.call_count == 3
    assert out == {"us": ["id-30"], "canada": ["id-31"], "japan": ["id-32"]}
