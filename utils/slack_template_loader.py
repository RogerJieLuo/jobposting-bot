import json
from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parent.parent

# Per-country template dir: templates/<country>/ (e.g. templates/canada/). Fallback: templates/default/
def _template_dir(country=None):
    key = (country or "default").strip().lower()
    return get_project_root() / "templates" / key

def load_template(template_name, country=None):
    root = get_project_root()
    d = _template_dir(country)
    path = d / template_name
    if not path.exists():
        path = _template_dir("default") / template_name
    with open(path, "r") as f:
        return f.read()

def render_template(template_name, variables: dict, country=None):
    template = json.loads(load_template(template_name, country))

    template["blocks"][0]["text"]["text"] = (
        f"*New Job Found!*\n"
        f"*Title:* {variables['title']}\n"
        f"*Company:* {variables['company']}\n"
        f"*Location:* {variables['location']}"
    )

    template["blocks"][1]["text"]["text"] = (
        f"*Summary:*\n{variables['summary']}"
    )

    template["blocks"][2]["elements"][0]["url"] = variables["link"]

    return template
