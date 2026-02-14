import time
import random
from utils.logger import logger
from crawler.linkedin_parser import parse_job_search_list, parse_job_applicant_and_description
from utils.http_client import get_html
from crawler.fetch_job_rules import is_target_software_role, is_under_100


logger.info("Fetching LinkedIn job list...")


def scan_jobs(keywords, location, limit_time):
    URL = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_TPR={limit_time}"
    html = get_html(URL)
    if not html:
        return []
    jobs = parse_job_search_list(html)
    logger.info(f"scan {len(jobs)} jobs")
    return jobs


def fetch_jobs(keywords, location, limit_time, max_jobs, country_key=None):
    jobs = scan_jobs(keywords, location, limit_time)
    filtered_jobs = []
    for job in jobs:
        if not is_target_software_role(job.title):
            continue
        job_html = get_html(job.url)

        (applicants, job_description) = parse_job_applicant_and_description(job_html)
        if not applicants:
            print("no applicant div: " + job.url)
        if not is_under_100(applicants):
            continue
        if not job_description:
            continue

        job.description = job_description
        job.country = country_key or "default"
        filtered_jobs.append(job)
        if len(filtered_jobs) >= max_jobs:
            break
        time.sleep(random.uniform(5, 10))
    return filtered_jobs


def fetch_jobs_for_locations(
    locations,
    keywords=None,
    limit_time="r3600",
    max_jobs_per_location=50,
    location_to_country=None,
):
    """
    locations: list of location strings (e.g. ["Canada", "United%20States", "Japan"]).
    location_to_country: optional dict mapping location -> country key (e.g. {"Canada": "canada", "Japan": "japan"}).
                         Used for per-country prompts and Slack templates. Fallback: "default".
    """
    location_to_country = location_to_country or {}
    all_jobs = []
    for loc in locations:
        country_key = location_to_country.get(loc, "default")
        logger.info(f"Fetching jobs for location: {loc} (country={country_key})")
        jobs = fetch_jobs(
            location=loc,
            keywords=keywords,
            limit_time=limit_time,
            max_jobs=max_jobs_per_location,
            country_key=country_key,
        )
        logger.info(f"Found {len(jobs)} verified jobs in {loc}")
        all_jobs.extend(jobs)

    return all_jobs
