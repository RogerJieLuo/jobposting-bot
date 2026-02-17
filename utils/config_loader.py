from pathlib import Path
import os

def get_project_root():
    return Path(__file__).resolve().parent.parent


def _load_secret(env_names, config_filename):
    for env_name in env_names:
        value = os.getenv(env_name, "").strip()
        if value:
            return value

    root = get_project_root()
    config_path = root / "config" / config_filename
    with open(config_path, "r") as f:
        return f.read().strip()


def load_slack_webhook():
    return _load_secret(
        env_names=("SLACK_WEBHOOK_URL", "SLACK_WEBHOOK"),
        config_filename="slack_webhook.txt",
    )


def load_gemini_api_key():
    return _load_secret(
        env_names=("GEMINI_API_KEY",),
        config_filename="gemini_api_key.txt",
    )


def load_ollama_api_key():
    return _load_secret(
        env_names=("OLLAMA_API_KEY",),
        config_filename="ollama_api_key.txt",
    )


def load_supabase_url():
    return _load_secret(
        env_names=("SUPABASE_URL",),
        config_filename="supabase_url.txt",
    )


def load_supabase_service_role_key():
    return _load_secret(
        env_names=("SUPABASE_SERVICE_ROLE_KEY",),
        config_filename="supabase_service_role_key.txt",
    )
