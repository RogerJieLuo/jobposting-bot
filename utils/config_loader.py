from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parent.parent

def load_slack_webhook():
    root = get_project_root()
    config_path = root / "config" / "slack_webhook.txt"

    with open(config_path, "r") as f:
        return f.read().strip()


def load_gemini_api_key():
    root = get_project_root()
    config_path = root / "config" / "gemini_api_key.txt"

    with open(config_path, "r") as f:
        return f.read().strip()


def load_ollama_api_key():
    root = get_project_root()
    config_path = root / "config" / "ollama_api_key.txt"

    with open(config_path, "r") as f:
        return f.read().strip()
