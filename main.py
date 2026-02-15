import traceback
import os
from utils.logger import logger
from utils.seen_jobs import save_seen_jobs, load_seen_jobs
from crawler.fetch_job import fetch_jobs_for_locations
from llm.service import analyze_job, analyze_jobs
from notify.slack_sender import send_slack_job


locations = ["Canada", "United%20States", "Japan"]
# Map LinkedIn location string -> country key for per-country prompts and Slack templates (see prompts/<country>/ and templates/<country>/)
location_to_country = {"Canada": "canada", "United%20States": "us", "Japan": "japan"}
keywords = "software%20engineer"
limit_time = "r3600"  # one hour
# Switch LLM provider here ("ollama" or "gemini"), or set env LLM_PROVIDER.
llm_provider = os.getenv("LLM_PROVIDER", "gemini")
# Toggle company screening prompt section and company analysis. ("1"=on, "0"=off)
enable_company_screening = os.getenv("ENABLE_COMPANY_SCREENING", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

def filter_already_seen(jobs, seen_by_country):
    """seen_by_country: dict of country_key -> set of job IDs."""
    filtered = []
    for job in jobs:
        country = (getattr(job, "country", None) or "default").strip().lower()
        job_id = job.id
        if job_id and job_id not in seen_by_country.get(country, set()):
            filtered.append(job)
    return filtered


def _country_key(job):
    return (getattr(job, "country", None) or "default").strip().lower()


def _send_and_mark_seen(job, answer, added_by_country):
    send_slack_job(
        title=job.title,
        company=job.company,
        location=job.location,
        summary=answer,
        link=job.url,
        country=getattr(job, "country", None),
    )
    country = _country_key(job)
    added_by_country.setdefault(country, []).append(job.id)
    save_seen_jobs({country: [job.id]})


def _process_gemini_batch(new_jobs, provider, include_company_screening, added_by_country):
    try:
        responses_by_id = analyze_jobs(
            new_jobs,
            provider=provider,
            include_company_screening=include_company_screening,
        )
    except Exception as e:
        logger.error(f"Batch analysis failed via {provider}: {e}")
        logger.error(traceback.format_exc())
        return

    for job in new_jobs:
        try:
            response = responses_by_id.get(job.id)
            if not response:
                logger.warning("No Gemini batch result for job id=%s", job.id)
                continue
            _send_and_mark_seen(job, response["answer"], added_by_country)
        except Exception as e:
            logger.error(f"Error sending Gemini batch job {job.id}: {job.url} \n{e}")
            logger.error(traceback.format_exc())


def _process_single_job(new_jobs, provider, include_company_screening, added_by_country):
    for job in new_jobs:
        try:
            response = analyze_job(
                job,
                provider=provider,
                include_company_screening=include_company_screening,
            )
            if not response:
                continue
            _send_and_mark_seen(job, response["answer"], added_by_country)
        except Exception as e:
            logger.error(f"Error analyzing job {job.id} via {provider}: {job.url} \n{e}")
            logger.error(traceback.format_exc())


def ask_llm(new_jobs, provider, include_company_screening=True):
    """Run selected LLM on new jobs; only persist seen job after successful Slack send."""
    added_by_country = {}
    provider_key = (provider or "").strip().lower()

    if provider_key == "gemini":
        _process_gemini_batch(new_jobs, provider, include_company_screening, added_by_country)
        return added_by_country

    _process_single_job(new_jobs, provider, include_company_screening, added_by_country)
    return added_by_country


def main():
    seen_by_country = load_seen_jobs()
    all_jobs = fetch_jobs_for_locations(
        locations=locations,
        keywords=keywords,
        limit_time=limit_time,
        location_to_country=location_to_country,
    )
    new_jobs = filter_already_seen(all_jobs, seen_by_country)

    added_by_country = ask_llm(
        new_jobs,
        provider=llm_provider,
        include_company_screening=enable_company_screening,
    )
    logger.info(
        "Job fetch & analyze done. provider=%s company_screening=%s sent=%d",
        llm_provider,
        enable_company_screening,
        sum(len(v) for v in added_by_country.values()),
    )

if __name__ == "__main__":
    main()
