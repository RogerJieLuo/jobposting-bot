import os
import ollama

from llm.prompt_builder import (
    load_profile,
    load_rules,
    build_prompt,
)
from llm.parsing import extract_recommendation
from utils.config_loader import load_ollama_api_key


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_WEB_SEARCH_ENABLED = os.getenv("OLLAMA_WEB_SEARCH_ENABLED", "0").strip() == "1"
OLLAMA_WEB_SEARCH_MAX_RESULTS = int(os.getenv("OLLAMA_WEB_SEARCH_MAX_RESULTS", "5"))


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


def _build_web_search_query(job, prompt: str) -> str:
    company = getattr(job, "company", "") or ""
    title = getattr(job, "title", "") or ""
    location = getattr(job, "location", "") or ""
    return (
        f"Job: {title}\nCompany: {company}\nLocation: {location}\n\n"
        f"If the job posting is a good fit to the Candidate?\n\n"
        f"{prompt}"
    ).strip()


def _web_search_answer(job, prompt: str) -> str:
    query = _build_web_search_query(job, prompt)
    api_key = load_ollama_api_key()
    if not api_key:
        raise ValueError("Ollama API key is empty. Please set config/ollama_api_key.txt")
    client = ollama.Client(
        host='https://ollama.com', 
        headers={'Authorization': f'Bearer {api_key}'}
    )
    response = client.web_search(query=query, max_results=OLLAMA_WEB_SEARCH_MAX_RESULTS)
    results = _to_results(response)
    if not results:
        return "No web search results."
    lines = []
    for idx, item in enumerate(results, start=1):
        title = _field(item, "title").strip()
        link = _field(item, "link").strip()
        content = _field(item, "content").strip()
        content = content[:300]
        lines.append(f"{idx}. {title}\n{link}\n{content}")
    text = "\n\n".join(lines)

    return {
            "link": job.url,
            "answer": text,
            "decision": extract_recommendation(text),
            "provider": "ollama",
        }


def _local_chat(job, prompt: str):
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

def analyze(job, include_company_screening=True):
    country = getattr(job, "country", None) or "default"
    profile = load_profile(country)
    rules = load_rules(country)
    company_context = ""
    prompt = build_prompt(
        job_description=job.description,
        candidate_profile=profile,
        rules=rules,
        company_name=getattr(job, "company", None) or "Unknown",
        company_screening_rules="",
        company_context=company_context,
        country=country,
        include_company_screening=False,
    )
    if OLLAMA_WEB_SEARCH_ENABLED:
        return _web_search_answer(job, prompt)

    return _local_chat(job, prompt)
