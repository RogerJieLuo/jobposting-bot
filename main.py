import traceback
import os
import sys
from utils.logger import logger
from utils.seen_jobs import save_seen_jobs, get_seen_job_ids_for_candidates
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
# If enabled, fallback to Ollama when Gemini fails. ("1"=on, "0"=off)
allow_ollama_fallback = os.getenv("ALLOW_OLLAMA_FALLBACK", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

def filter_already_seen(jobs, seen_by_country):
    """seen_by_country: dict of country_key -> set of job IDs."""
    filtered = []
    global_seen = seen_by_country.get("default", set())
    for job in jobs:
        country = (getattr(job, "country", None) or "default").strip().lower()
        job_id = job.id
        country_seen = seen_by_country.get(country, set())
        if job_id and job_id not in country_seen and job_id not in global_seen:
            filtered.append(job)
    return filtered


def _country_key(job):
    return (getattr(job, "country", None) or "default").strip().lower()


def _group_jobs_by_country(jobs):
    grouped = {}
    for job in jobs:
        grouped.setdefault(_country_key(job), []).append(job)
    return grouped


def _build_seen_rank_payload(response):
    if not isinstance(response, dict):
        return {}
    rank = {}
    for key in ("provider", "decision", "score", "rank", "recommendation"):
        value = response.get(key)
        if value is not None:
            rank[key] = value
    return rank


def _send_and_mark_seen(job, response, added_by_country):
    answer = response["answer"]
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
    save_seen_jobs(
        {
            country: [
                {
                    "job_title": job.title,
                    "job_id": str(job.id),
                    "url": job.url,
                    "company": job.company,
                    "location": job.location,
                    "job_description": job.description,
                    "rank": _build_seen_rank_payload(response),
                }
            ]
        }
    )


def _process_gemini_batch(new_jobs, provider, include_company_screening, added_by_country):
    logger.info(
        "LLM analyze start: provider=%s mode=batch jobs=%d",
        provider,
        len(new_jobs),
    )
    failed_jobs = []
    grouped_jobs = _group_jobs_by_country(new_jobs)

    grouped_items = list(grouped_jobs.items())
    for idx, (country, country_jobs) in enumerate(grouped_items):
        try:
            responses_by_id = analyze_jobs(
                country_jobs,
                provider=provider,
                include_company_screening=include_company_screening,
            )
            logger.info(
                "LLM analyze success: provider=%s mode=batch country=%s jobs=%d",
                provider,
                country,
                len(country_jobs),
            )
        except Exception as e:
            logger.error(
                "Batch analysis failed via %s for country=%s jobs=%d: %s",
                provider,
                country,
                len(country_jobs),
                e,
            )
            logger.error(traceback.format_exc())
            failed_jobs.extend(country_jobs)
            # Fail fast: once Gemini fails for one country, hand all remaining jobs to fallback provider.
            for _, remaining_jobs in grouped_items[idx + 1 :]:
                failed_jobs.extend(remaining_jobs)
            logger.warning(
                "Gemini failed once; skipping remaining Gemini countries and deferring %d jobs to fallback.",
                len(failed_jobs),
            )
            break

        for job in country_jobs:
            try:
                response = responses_by_id.get(job.id)
                if not response:
                    logger.warning("No Gemini batch result for job id=%s", job.id)
                    failed_jobs.append(job)
                    continue
                _send_and_mark_seen(job, response, added_by_country)
            except Exception as e:
                logger.error(f"Error sending Gemini batch job {job.id}: {job.url} \n{e}")
                logger.error(traceback.format_exc())
    return failed_jobs


def _process_single_job(new_jobs, provider, include_company_screening, added_by_country):
    logger.info(
        "LLM analyze start: provider=%s mode=single jobs=%d",
        provider,
        len(new_jobs),
    )
    for job in new_jobs:
        try:
            response = analyze_job(
                job,
                provider=provider,
                include_company_screening=include_company_screening,
            )
        except Exception as e:
            logger.error(f"Error analyzing job {job.id} via {provider}: {job.url} \n{e}")
            logger.error(traceback.format_exc())
            continue

        if not response:
            continue

        try:
            _send_and_mark_seen(job, response, added_by_country)
        except Exception as e:
            logger.error(f"Error sending job {job.id} via {provider}: {job.url} \n{e}")
            logger.error(traceback.format_exc())


def ask_llm(new_jobs, provider, include_company_screening=True):
    """Run selected LLM on new jobs; only persist seen job after successful Slack send."""
    added_by_country = {}
    provider_key = (provider or "").strip().lower()
    logger.info(
        "LLM selection: primary=%s allow_ollama_fallback=%s jobs=%d",
        provider_key,
        allow_ollama_fallback,
        len(new_jobs),
    )

    if provider_key == "gemini":
        failed_jobs = _process_gemini_batch(
            new_jobs,
            provider,
            include_company_screening,
            added_by_country,
        )
        if failed_jobs:
            if allow_ollama_fallback:
                logger.warning(
                    "Gemini failed for %d jobs; fallback to Ollama is enabled (ALLOW_OLLAMA_FALLBACK=1).",
                    len(failed_jobs),
                )
                logger.info("LLM selection: fallback provider=ollama")
                _process_single_job(
                    failed_jobs,
                    provider="ollama",
                    include_company_screening=include_company_screening,
                    added_by_country=added_by_country,
                )
            else:
                logger.warning(
                    "Gemini failed for %d jobs; fallback to Ollama is disabled (ALLOW_OLLAMA_FALLBACK=0).",
                    len(failed_jobs),
                )
        return added_by_country

    _process_single_job(new_jobs, provider, include_company_screening, added_by_country)
    return added_by_country


def main():
    all_jobs = fetch_jobs_for_locations(
        locations=locations,
        keywords=keywords,
        limit_time=limit_time,
        location_to_country=location_to_country,
    )
    candidate_job_ids = [str(job.id) for job in all_jobs if getattr(job, "id", None)]
    seen_job_ids = get_seen_job_ids_for_candidates(candidate_job_ids)
    new_jobs = [job for job in all_jobs if job.id and str(job.id) not in seen_job_ids]
    logger.info(
        "Dedup result: total=%d seen=%d new=%d",
        len(all_jobs),
        len(seen_job_ids),
        len(new_jobs),
    )

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
    try:
        main()
    except Exception as e:
        print(f"Job posting app failed: {e}")
        sys.exit(0)
