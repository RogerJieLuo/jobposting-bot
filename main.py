from logger_util import logger
from job_file import save_seen_jobs, load_seen_jobs, write_job_to_csv
from scripts.fetch_job import fetch_jobs_for_locations
from llm.ask_ollama import analyze_with_ollama


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


def main():
    seen_jobs = load_seen_jobs()

    all_jobs = fetch_jobs_for_locations(locations=locations, keywords=keywords, limit_time=limit_time, max_jobs_per_location=max_jobs_per_location)

    new_jobs = filter_already_seen(all_jobs, seen_jobs)

    # Ollama analyze
    ollama_responses = []
    for job in new_jobs:
        try:
            response = analyze_with_ollama(job)
            write_job_to_csv(response)
            
            seen_jobs.add(job.id)
        except Exception as e:
            logger.error(f"Error analyzing job {job.id}: {e}")

    save_seen_jobs(seen_jobs)
    logger.info("Job fetch & analyze done.")

if __name__ == "__main__":
    main()
