import os
import ollama

from llm.prompt_builder import (
    load_profile,
    load_rules,
    load_company_screening_rules,
    build_prompt,
)
from llm.parsing import extract_recommendation


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
DEFAULT_WEB_SEARCH_RESULTS = int(os.getenv("OLLAMA_WEB_SEARCH_MAX_RESULTS", "3"))


def _to_results(response):
    if response is None:
        return []
    if hasattr(response, "results"):
        return getattr(response, "results") or []
    if isinstance(response, dict):
        return response.get("results") or []
    return []


def _field(item, key):
    if hasattr(item, key):
        return getattr(item, key) or ""
    if isinstance(item, dict):
        return item.get(key, "") or ""
    return ""


def web_search_company_context(company_name, max_results=DEFAULT_WEB_SEARCH_RESULTS):
    if not company_name:
        return "Company name not provided."

    query = (
        f"{company_name} company overview, business model, recent layoffs, "
        f"funding status, engineering reputation"
    )
    try:
        client = ollama.Client()
        response = client.web_search(query=query, max_results=max_results)
    except Exception as e:
        return f"Web search unavailable: {e}"

    results = _to_results(response)
    if not results:
        return "No web results found for company."

    lines = []
    for idx, item in enumerate(results, start=1):
        title = _field(item, "title").strip()
        link = _field(item, "link").strip()
        content = _field(item, "content").strip()
        content = content[:220]
        lines.append(f"{idx}. {title} | {link}\n   {content}")
    return "\n".join(lines)


def analyze(job, include_company_screening=True):
    country = getattr(job, "country", None) or "default"
    profile = load_profile(country)
    rules = load_rules(country)
    company_rules = ""
    company_context = ""
    if include_company_screening:
        company_rules = load_company_screening_rules(country)
        company_context = web_search_company_context(getattr(job, "company", None))
    prompt = build_prompt(
        job_description=job.description,
        candidate_profile=profile,
        rules=rules,
        company_name=getattr(job, "company", None) or "Unknown",
        company_screening_rules=company_rules,
        company_context=company_context,
        country=country,
        include_company_screening=include_company_screening,
    )
    messages = [
        {
            "role": "system",
            "content": "You are a professional career advisor and job matching assistant for a backend software engineer.",
        },
        {"role": "user", "content": prompt},
    ]
    response = ollama.chat(model=DEFAULT_MODEL, messages=messages)
    text = response["message"]["content"]
    return {
        "link": job.url,
        "answer": text,
        "decision": extract_recommendation(text),
        "provider": "ollama",
    }
