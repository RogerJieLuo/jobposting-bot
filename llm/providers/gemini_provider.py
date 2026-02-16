import os
import json
import re
from google import genai
from google.genai import types

from llm.prompt_builder import (
    load_profile,
    load_rules,
    load_company_screening_rules,
    load_gemini_batch_prompt_template,
    build_prompt,
)
from llm.parsing import extract_recommendation
from utils.config_loader import load_gemini_api_key


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
MAX_BATCH_JOBS = int(os.getenv("GEMINI_BATCH_MAX_JOBS", "12"))
MAX_BATCH_PROMPT_CHARS = int(os.getenv("GEMINI_BATCH_MAX_PROMPT_CHARS", "60000"))


def _build_company_context(company_name: str) -> str:
    if not company_name:
        return "Company name not provided."
    return (
        f"Company under evaluation: {company_name}. "
        "Use your model knowledge to assess company quality/risk."
    )


def analyze(job, include_company_screening):
    api_key = load_gemini_api_key()
    if not api_key:
        raise ValueError("Gemini API key is empty. Please set config/gemini_api_key.txt")

    country = getattr(job, "country", None) or "default"
    profile = load_profile(country)
    rules = load_rules(country)
    company_rules = load_company_screening_rules(country) if include_company_screening else ""
    prompt = build_prompt(
        job_description=job.description,
        candidate_profile=profile,
        rules=rules,
        company_name=getattr(job, "company", None) or "Unknown",
        company_screening_rules=company_rules,
        company_context=(
            _build_company_context(getattr(job, "company", None)) if include_company_screening else ""
        ),
        country=country,
        include_company_screening=include_company_screening,
    )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(googleSearch=types.GoogleSearch())
            ]
        ),
    )
    text = (getattr(response, "text", None) or "").strip()
    return {
        "link": job.url,
        "answer": text,
        "decision": extract_recommendation(text),
        "provider": "gemini",
    }


def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` wrapper so Gemini JSON output can be parsed safely."""
    if not text:
        return ""
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


def _parse_batch_response(text: str):
    raw = _strip_code_fence(text)
    if not raw:
        return []
    data = json.loads(raw)
    if isinstance(data, dict):
        items = data.get("jobs") or data.get("results") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []
    return items if isinstance(items, list) else []


def _build_job_block(job) -> str:
    description = (getattr(job, "description", None) or "").strip()
    if len(description) > 3000:
        description = description[:3000] + "\n...[truncated]"
    return (
        f"JOB_ID: {job.id}\n"
        f"TITLE: {job.title}\n"
        f"COMPANY: {job.company}\n"
        f"LOCATION: {job.location}\n"
        f"URL: {job.url}\n"
        f"DESCRIPTION:\n{description}\n"
    )


def _load_api_key() -> str:
    api_key = load_gemini_api_key()
    if not api_key:
        raise ValueError("Gemini API key is empty. Please set config/gemini_api_key.txt")
    return api_key


def _build_prompt_for_jobs(jobs, include_company_screening) -> str:
    country = (getattr(jobs[0], "country", None) or "default").strip().lower()
    profile = load_profile(country)
    rules = load_rules(country)
    company_rules = load_company_screening_rules(country) if include_company_screening else ""
    jobs_block = "\n---\n".join(_build_job_block(job) for job in jobs)
    template = load_gemini_batch_prompt_template(
        country=country,
        include_company_screening=include_company_screening,
    )
    return template.format(
        candidate_profile=profile,
        evaluation_rules=rules,
        company_screening_rules=company_rules,
        jobs_block=jobs_block,
    )


def _request_batch(prompt: str, api_key: str):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(googleSearch=types.GoogleSearch())],
        ),
    )
    text = (getattr(response, "text", None) or "").strip()
    return _parse_batch_response(text)


def _build_answer_from_item(item: dict) -> tuple[str, str]:
    recommendation = str(item.get("recommendation") or item.get("decision") or "").strip()
    summary = str(item.get("summary") or item.get("reason") or "").strip()
    score = item.get("score")
    rank = item.get("rank")
    company_verdict = str(item.get("company_verdict") or "").strip()
    head = f"Clear recommendation: {recommendation}"
    if score is not None:
        head += f", match score {score}"
    extras = []
    if rank is not None:
        extras.append(f"Rank: {rank}")
    if company_verdict:
        extras.append(f"Company verdict: {company_verdict}")
    answer_parts = [head]
    if extras:
        answer_parts.append("\n".join(extras))
    if summary:
        answer_parts.append(summary)
    answer = "\n".join(answer_parts).strip()
    decision = extract_recommendation(recommendation) or extract_recommendation(answer)
    return answer, decision


def _map_items_to_results(items, jobs):
    by_id = {}
    jobs_by_id = {job.id: job for job in jobs if getattr(job, "id", None)}
    for item in items:
        if not isinstance(item, dict):
            continue
        job_id = str(item.get("job_id") or item.get("id") or "").strip()
        if not job_id or job_id not in jobs_by_id:
            continue
        answer, decision = _build_answer_from_item(item)
        by_id[job_id] = {
            "link": jobs_by_id[job_id].url,
            "answer": answer,
            "decision": decision,
            "provider": "gemini",
        }
    return by_id


def _chunk_jobs(jobs, include_company_screening):
    chunks = []
    current = []
    for job in jobs:
        candidate = current + [job]
        if len(candidate) > MAX_BATCH_JOBS:
            if current:
                chunks.append(current)
                current = [job]
            else:
                chunks.append(candidate)
                current = []
            continue

        prompt = _build_prompt_for_jobs(candidate, include_company_screening=include_company_screening)
        if len(prompt) > MAX_BATCH_PROMPT_CHARS and current:
            chunks.append(current)
            current = [job]
            continue
        current = candidate

    if current:
        chunks.append(current)
    return chunks


def analyze_batch(jobs, include_company_screening):
    if not jobs:
        return {}
    api_key = _load_api_key()
    chunks = _chunk_jobs(jobs, include_company_screening=include_company_screening)
    all_results = {}
    for chunk in chunks:
        prompt = _build_prompt_for_jobs(chunk, include_company_screening=include_company_screening)
        items = _request_batch(prompt, api_key)
        all_results.update(_map_items_to_results(items, chunk))
    return all_results
