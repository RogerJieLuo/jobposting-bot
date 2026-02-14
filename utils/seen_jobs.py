from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEEN_FILE = PROJECT_ROOT / "seen_jobs.txt"


def load_seen_jobs():
    if SEEN_FILE.exists():
        return set(line.strip() for line in SEEN_FILE.read_text().splitlines())
    return set()


def save_seen_jobs(seen_jobs):
    SEEN_FILE.write_text("\n".join(job_id for job_id in seen_jobs))
