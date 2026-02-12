from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parent.parent

def load_slack_webhook():
    root = get_project_root()
    config_path = root / "config" / "slack_webhook.txt"

    with open(config_path, "r") as f:
        return f.read().strip()
