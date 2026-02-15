import time
import random
from utils.logger import logger
from crawler.linkedin_parser import (
    parse_job_search_list,
    parse_job_applicant_and_description,
    PAGE_SIZE,
)
from utils.http_client import get_html
from crawler.fetch_job_rules import is_target_software_role, is_under_100

logger.info("Fetching LinkedIn job list...")

MAX_PAGES_PER_LOCATION = 200
MAX_STUCK_PAGES = 3


def scan_jobs(keywords, location, limit_time, start=0):
    """Fetch one page of job listings. start=0 is first page, start=25 second, etc."""
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={keywords}&location={location}&f_TPR={limit_time}&start={start}"
    )
    logger.info(f"Start scaning url: {url}")
    html = get_html(url)
    if not html:
        return []
    jobs = parse_job_search_list(html)
    logger.info(f"scan page start={start}: {len(jobs)} jobs")
    return jobs


def fetch_jobs(keywords, location, limit_time, max_jobs, country_key=None):
    """
    Collect up to max_jobs unique (deduplicated) jobs per location.
    Paginate through search results until we have enough or there are no more.
    """
    filtered_jobs = []
    seen_listing_ids = set()  # dedupe all listed jobs within this location (even non-matching ones)
    seen_page_signatures = set()
    stuck_pages = 0
    pages_scanned = 0
    start = 0

    while len(filtered_jobs) < max_jobs:
        if pages_scanned >= MAX_PAGES_PER_LOCATION:
            logger.warning(
                "Stop pagination for %s after %d pages (safety cap).",
                location,
                MAX_PAGES_PER_LOCATION,
            )
            break
        page_jobs = scan_jobs(keywords, location, limit_time, start=start)
        pages_scanned += 1
        if not page_jobs:
            break

        page_signature = tuple(job.id for job in page_jobs if job.id)
        if page_signature and page_signature in seen_page_signatures:
            logger.warning(
                "Detected repeated page content for %s at start=%d; stop pagination.",
                location,
                start,
            )
            break
        if page_signature:
            seen_page_signatures.add(page_signature)

        new_listing_count = 0
        for job in page_jobs:
            if len(filtered_jobs) >= max_jobs:
                break
            if not job.id:
                continue
            if job.id in seen_listing_ids:
                continue
            seen_listing_ids.add(job.id)
            new_listing_count += 1
            if not is_target_software_role(job.title):
                continue

            job_html = get_html(job.url)
            if not job_html:
                continue
            applicants, job_description = parse_job_applicant_and_description(job_html)
            if not applicants:
                logger.info("No applicant info: %s", job.url)
            if not is_under_100(applicants):
                continue
            if not job_description:
                continue

            job.description = job_description
            job.country = country_key or "default"
            filtered_jobs.append(job)

            time.sleep(random.uniform(5, 10))

        if new_listing_count == 0:
            stuck_pages += 1
            if stuck_pages >= MAX_STUCK_PAGES:
                logger.warning(
                    "No new listings detected for %s across %d pages; stop pagination.",
                    location,
                    MAX_STUCK_PAGES,
                )
                break
        else:
            stuck_pages = 0

        start += PAGE_SIZE

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
    max_jobs_per_location: max unique jobs to fetch per location (paginates until reached or no more).
    location_to_country: optional dict mapping location -> country key (e.g. {"Canada": "canada", "Japan": "japan"}).
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
        logger.info(f"Found {len(jobs)} verified unique jobs in {loc}")
        all_jobs.extend(jobs)

    return all_jobs
