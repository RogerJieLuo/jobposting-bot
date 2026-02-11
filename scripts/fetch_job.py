import time
from logger_util import logger
from scripts.linkedin_parser import parse_job_search_list, parse_job_applicant_and_description
from open_url import get_html
from scripts.fetch_job_rules import is_target_software_role, is_under_100
import random


logger.info("Fetching LinkedIn job list...")


def scan_jobs(keywords, location, limit_time):
    URL = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_TPR={limit_time}"
    html = get_html(URL)
    if not html:
        return []
    jobs = parse_job_search_list(html)
    logger.info(f"scan {len(jobs)} jobs")
    return jobs


def fetch_jobs(keywords, location, limit_time, max_jobs):
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
        filtered_jobs.append(job)
        if len(filtered_jobs) >= max_jobs:
            break
        time.sleep(random.uniform(5, 10))
    return filtered_jobs


def fetch_jobs_for_locations(locations, keywords=None, limit_time="r3600", max_jobs_per_location=50):
    all_jobs = []
    for loc in locations:
        logger.info(f"Fetching jobs for location: {loc}")
        jobs = fetch_jobs(location=loc, keywords=keywords, limit_time=limit_time, max_jobs=max_jobs_per_location)
        logger.info(f"Found {len(jobs)} verified jobs in {loc}")
        all_jobs.extend(jobs)

    return all_jobs

