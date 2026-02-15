import os

from llm.providers.ollama_provider import analyze as analyze_with_ollama
from llm.providers.gemini_provider import analyze as analyze_with_gemini, analyze_batch as analyze_batch_with_gemini


SUPPORTED_LLM_PROVIDERS = ("ollama", "gemini")


def normalize_provider(provider: str) -> str:
    p = (provider or "").strip().lower()
    if p not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {SUPPORTED_LLM_PROVIDERS}")
    return p


def get_default_provider() -> str:
    return normalize_provider(os.getenv("LLM_PROVIDER", "ollama"))


def analyze_job(job, provider: str, include_company_screening=True):
    p = normalize_provider(provider)
    if p == "ollama":
        return analyze_with_ollama(job, include_company_screening=include_company_screening)
    return analyze_with_gemini(job, include_company_screening=include_company_screening)


def analyze_jobs(jobs, provider: str, include_company_screening=False):
    p = normalize_provider(provider)
    if p == "gemini":
        grouped = {}
        for job in jobs:
            country = (getattr(job, "country", None) or "default").strip().lower()
            grouped.setdefault(country, []).append(job)
        out = {}
        for country_jobs in grouped.values():
            out.update(
                analyze_batch_with_gemini(
                    country_jobs,
                    include_company_screening=include_company_screening,
                )
            )
        return out
    elif p == "ollama":
        out = {}
        for job in jobs:
            if not getattr(job, "id", None):
                continue
            out[job.id] = analyze_with_ollama(job, include_company_screening=include_company_screening)
        return out
    else:
        # Defensive branch; normalize_provider already guards this.
        raise ValueError(f"Unsupported LLM provider: {provider}")
