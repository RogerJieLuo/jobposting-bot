"""Unit tests for utils.config_loader."""
from pathlib import Path
from unittest.mock import patch, mock_open
from utils.config_loader import get_project_root, load_slack_webhook


def test_get_project_root():
    root = get_project_root()
    assert root.name == "jobposting"
    assert (root / "utils").is_dir()


def test_load_slack_webhook_returns_stripped_content():
    fake_webhook = "https://hooks.slack.com/services/abc/123"
    with patch("utils.config_loader.get_project_root", return_value=Path("/fake/root")):
        with patch("builtins.open", mock_open(read_data=fake_webhook + "\n")):
            result = load_slack_webhook()
    assert result == fake_webhook
