"""Unit tests for utils.config_loader."""
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from utils.config_loader import (
    get_project_root,
    load_slack_webhook,
    load_gemini_api_key,
    load_ollama_api_key,
    load_supabase_url,
    load_supabase_service_role_key,
)


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


def test_load_gemini_api_key_returns_stripped_content():
    fake_key = "AIzaSyFakeKey"
    with patch("utils.config_loader.get_project_root", return_value=Path("/fake/root")):
        with patch("builtins.open", mock_open(read_data=fake_key + "\n")):
            result = load_gemini_api_key()
    assert result == fake_key


def test_load_ollama_api_key_returns_stripped_content():
    fake_key = "ollama-key-abc"
    with patch("utils.config_loader.get_project_root", return_value=Path("/fake/root")):
        with patch("builtins.open", mock_open(read_data=fake_key + "\n")):
            result = load_ollama_api_key()
    assert result == fake_key


def test_load_slack_webhook_uses_env_first():
    with patch.dict(os.environ, {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/from/env"}, clear=False):
        with patch("builtins.open") as mock_file:
            result = load_slack_webhook()
    assert result == "https://hooks.slack.com/services/from/env"
    mock_file.assert_not_called()


def test_load_gemini_api_key_uses_env_first():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "env-gemini-key"}, clear=False):
        with patch("builtins.open") as mock_file:
            result = load_gemini_api_key()
    assert result == "env-gemini-key"
    mock_file.assert_not_called()


def test_load_ollama_api_key_uses_env_first():
    with patch.dict(os.environ, {"OLLAMA_API_KEY": "env-ollama-key"}, clear=False):
        with patch("builtins.open") as mock_file:
            result = load_ollama_api_key()
    assert result == "env-ollama-key"
    mock_file.assert_not_called()


def test_load_supabase_url_returns_stripped_content():
    fake_url = "https://abc.supabase.co"
    with patch("utils.config_loader.get_project_root", return_value=Path("/fake/root")):
        with patch("builtins.open", mock_open(read_data=fake_url + "\n")):
            result = load_supabase_url()
    assert result == fake_url


def test_load_supabase_service_role_key_returns_stripped_content():
    fake_key = "service-role-key"
    with patch("utils.config_loader.get_project_root", return_value=Path("/fake/root")):
        with patch("builtins.open", mock_open(read_data=fake_key + "\n")):
            result = load_supabase_service_role_key()
    assert result == fake_key


def test_load_supabase_url_uses_env_first():
    with patch.dict(os.environ, {"SUPABASE_URL": "https://env.supabase.co"}, clear=False):
        with patch("builtins.open") as mock_file:
            result = load_supabase_url()
    assert result == "https://env.supabase.co"
    mock_file.assert_not_called()


def test_load_supabase_service_role_key_uses_env_first():
    with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": "env-service-role-key"}, clear=False):
        with patch("builtins.open") as mock_file:
            result = load_supabase_service_role_key()
    assert result == "env-service-role-key"
    mock_file.assert_not_called()
