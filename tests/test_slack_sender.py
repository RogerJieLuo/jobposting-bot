"""Unit tests for notify.slack_sender."""
from unittest.mock import patch, MagicMock
from notify.slack_sender import send_slack_job


def test_send_slack_job_calls_webhook_with_rendered_payload():
    with patch("notify.slack_sender.load_slack_webhook", return_value="https://hooks.slack.com/fake"):
        with patch("notify.slack_sender.render_template", return_value={"blocks": []}) as mock_render:
            with patch("notify.slack_sender.requests.post") as mock_post:
                send_slack_job(
                    title="Engineer",
                    company="Acme",
                    location="Toronto",
                    summary="Apply.",
                    link="https://linkedin.com/jobs/1",
                    country="canada",
                )
    mock_render.assert_called_once()
    call_args, call_kw = mock_render.call_args
    assert call_args[0] == "slack_job_template.json"
    assert call_args[1]["title"] == "Engineer"
    assert call_args[1]["link"] == "https://linkedin.com/jobs/1"
    assert call_kw["country"] == "canada"
    mock_post.assert_called_once_with("https://hooks.slack.com/fake", json={"blocks": []})


def test_send_slack_job_truncates_summary():
    with patch("notify.slack_sender.load_slack_webhook", return_value="https://hooks.slack.com/fake"):
        with patch("notify.slack_sender.render_template", return_value={}) as mock_render:
            with patch("notify.slack_sender.requests.post"):
                long_summary = "x" * 1000
                send_slack_job(
                    title="T",
                    company="C",
                    location="L",
                    summary=long_summary,
                    link="https://x.com",
                    country=None,
                )
    # Summary should be truncated to 800 chars (variables dict is 2nd positional arg)
    variables = mock_render.call_args[0][1]
    assert len(variables["summary"]) == 800
