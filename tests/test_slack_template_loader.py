"""Unit tests for utils.slack_template_loader."""
import json
from pathlib import Path
from utils.slack_template_loader import (
    get_project_root,
    load_template,
    render_template,
    _template_dir,
)


def test_get_project_root():
    root = get_project_root()
    assert root.name == "jobposting"
    assert (root / "utils").is_dir()


def test_template_dir_default():
    root = get_project_root()
    assert _template_dir(None) == root / "templates" / "default"
    assert _template_dir("default") == root / "templates" / "default"


def test_template_dir_country():
    root = get_project_root()
    assert _template_dir("canada") == root / "templates" / "canada"
    assert _template_dir("Japan") == root / "templates" / "japan"


def test_load_template_default():
    content = load_template("slack_job_template.json", country=None)
    data = json.loads(content)
    assert "blocks" in data
    assert len(data["blocks"]) >= 2


def test_load_template_fallback_to_default_when_country_missing():
    # Non-existent country should fall back to default
    content = load_template("slack_job_template.json", country="nonexistent_country_xyz")
    data = json.loads(content)
    assert "blocks" in data


def test_render_template_injects_variables():
    variables = {
        "title": "Backend Engineer",
        "company": "Acme",
        "location": "Remote",
        "summary": "Match score 85. Apply.",
        "link": "https://linkedin.com/jobs/123",
    }
    payload = render_template("slack_job_template.json", variables, country=None)
    assert payload["blocks"][0]["text"]["text"] == (
        "*New Job Found!*\n"
        "*Title:* Backend Engineer\n"
        "*Company:* Acme\n"
        "*Location:* Remote"
    )
    assert "Match score 85" in payload["blocks"][1]["text"]["text"]
    assert payload["blocks"][2]["elements"][0]["url"] == "https://linkedin.com/jobs/123"
