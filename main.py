import traceback
from utils.logger import logger
from utils.seen_jobs import save_seen_jobs, load_seen_jobs
from crawler.fetch_job import fetch_jobs_for_locations
from llm.ask_ollama import analyze_with_ollama
from notify.slack_sender import send_slack_job


locations = ["Canada", "United%20States", "Japan"]
# Map LinkedIn location string -> country key for per-country prompts and Slack templates (see prompts/<country>/ and templates/<country>/)
location_to_country = {"Canada": "canada", "United%20States": "us", "Japan": "japan"}
keywords = "software%20engineer"
max_jobs_per_location = 2
limit_time = "r3600"  # one hour

def filter_already_seen(jobs, seen_by_country):
    """seen_by_country: dict of country_key -> set of job IDs."""
    filtered = []
    for job in jobs:
        country = (getattr(job, "country", None) or "default").strip().lower()
        job_id = job.id
        if job_id and job_id not in seen_by_country.get(country, set()):
            filtered.append(job)
    return filtered


def ask_ollama(new_jobs):
    """Run Ollama on new jobs; only persist seen job after successful Slack send."""
    added_by_country = {}
    for job in new_jobs:
        try:
            response = analyze_with_ollama(job)
            if not response:
                continue
            send_slack_job(
                title=job.title,
                company=job.company,
                location=job.location,
                summary=response['ollama_answer'],
                link=job.url,
                country=getattr(job, "country", None),
            )
            country = (getattr(job, "country", None) or "default").strip().lower()
            added_by_country.setdefault(country, []).append(job.id)
            # Persist immediately after successful Slack send to avoid duplicate resend after crashes.
            save_seen_jobs({country: [job.id]})
        except Exception as e:
            logger.error(f"Error analyzing job {job.id}: {job.url} \n{e}")
            logger.error(traceback.format_exc())
    return added_by_country


def main():
    seen_by_country = load_seen_jobs()
    all_jobs = fetch_jobs_for_locations(
        locations=locations,
        keywords=keywords,
        limit_time=limit_time,
        max_jobs_per_location=max_jobs_per_location,
        location_to_country=location_to_country,
    )
    new_jobs = filter_already_seen(all_jobs, seen_by_country)

    added_by_country = ask_ollama(new_jobs)
    logger.info("Job fetch & analyze done. sent=%d", sum(len(v) for v in added_by_country.values()))

if __name__ == "__main__":
    main()
