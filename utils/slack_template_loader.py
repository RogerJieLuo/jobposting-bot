import json
from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parent.parent

def load_template(template_name):
    root = get_project_root()
    template_path = root / "templates" / template_name

    with open(template_path, "r") as f:
        return f.read()

def render_template(template_name, variables: dict):
    template = json.loads(load_template(template_name))

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
