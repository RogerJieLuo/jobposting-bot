import traceback
from logger_util import logger
from job_file import save_seen_jobs, load_seen_jobs
from scripts.fetch_job import fetch_jobs_for_locations
from llm.ask_ollama import analyze_with_ollama
from notify.slack_sender import send_slack_job


locations = ["Canada", "United%20States", "Japan"]
keywords = "software%20engineer" 
max_jobs_per_location = 2 
limit_time = "r3600" # one hour

def filter_already_seen(jobs, seen_jobs):
    filtered = []
    for job in jobs:
        job_id = job.id  
        if job_id not in seen_jobs:
            filtered.append(job)
    return filtered


def ask_ollama(new_jobs, seen_jobs):
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
                link=job.url
            )

            seen_jobs.add(job.id)
        except Exception as e:
            logger.error(f"Error analyzing job {job.id}: {job.url} \n{e}")
            logger.error(traceback.format_exc())


def main():
    seen_jobs = load_seen_jobs()
    all_jobs = fetch_jobs_for_locations(locations=locations, keywords=keywords, limit_time=limit_time, max_jobs_per_location=max_jobs_per_location)
    new_jobs = filter_already_seen(all_jobs, seen_jobs)
    
    ask_ollama(new_jobs, seen_jobs)
    # save_seen_jobs(seen_jobs)
    logger.info("Job fetch & analyze done.")

if __name__ == "__main__":
    main()
