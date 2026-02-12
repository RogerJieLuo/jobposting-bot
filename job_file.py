import os

SEEN_FILE = os.path.join(os.path.dirname(__file__), 'seen_jobs.txt')

def load_seen_jobs():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_seen_jobs(seen_jobs):
    with open(SEEN_FILE, 'w') as f:
        for job_id in seen_jobs:
            f.write(job_id + '\n')

