import requests
from utils.slack_template_loader import render_template
from utils.config_loader import load_slack_webhook

def send_slack_job(title, company, location, summary, link, country=None):
    webhook = load_slack_webhook()
    
    payload = render_template(
        "slack_job_template.json",
        {
            "title": title,
            "company": company,
            "location": location,
            "summary": summary[:800],  # length control
            "link": link
        },
        country=country,
    )

    response = requests.post(webhook, json=payload)
    # print(response.status_code)
    # print(response.text)
