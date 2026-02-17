from pathlib import Path

from utils.logger import logger
from database import seen_jobs_repository

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEEN_DIR = PROJECT_ROOT / "seen_jobs"

# Cap size per country so files don't grow forever. Oldest entries are dropped.
MAX_SEEN = 50_000


def _country_file(country: str) -> Path:
    key = (country or "default").strip().lower()
    return SEEN_DIR / f"{key}.txt"


def load_seen_jobs():
    """
    Load seen job IDs per country. Returns dict: country_key -> set of job IDs.
    """
    try:
        data = seen_jobs_repository.load_seen_jobs()
        if data is not None:
            total = len(data.get("default", set()))
            logger.info("Loaded seen jobs from database count=%d", total)
            return data
    except Exception as e:
        logger.error("Database load_seen_jobs failed; fallback to local files: %s", e)

    result = {}
    if not SEEN_DIR.exists():
        return result
    for path in SEEN_DIR.glob("*.txt"):
        country = path.stem.lower()
        lines = [
            line.strip()
            for line in path.read_text().splitlines()
            if line.strip()
        ]
        if len(lines) > MAX_SEEN:
            lines = lines[-MAX_SEEN:]
            path.write_text("\n".join(lines))
        result[country] = set(lines)
    return result


def get_seen_urls_for_candidates(urls):
    """
    Return seen job IDs only for the candidate ID list.
    Uses Supabase incremental query first; falls back to local files.
    """
    candidates = {str(v).strip() for v in (urls or []) if str(v).strip()}
    if not candidates:
        return set()

    try:
        found = seen_jobs_repository.find_existing_job_ids(sorted(candidates))
        if found is not None:
            logger.info(
                "Checked seen job IDs via database candidates=%d found=%d",
                len(candidates),
                len(found),
            )
            return found
    except Exception as e:
        logger.error("Database get_seen_job_ids_for_candidates failed; fallback to local files: %s", e)

    local_seen = set()
    if not SEEN_DIR.exists():
        return local_seen
    for path in SEEN_DIR.glob("*.txt"):
        lines = {line.strip() for line in path.read_text().splitlines() if line.strip()}
        local_seen.update(lines)
    return candidates.intersection(local_seen)


def save_seen_jobs(added_by_country: dict[str, list]):
    """
    Persist seen jobs. added_by_country: country_key -> list of job URLs or dict rows.
    """
    if not added_by_country:
        return

    try:
        saved = seen_jobs_repository.save_seen_jobs(added_by_country)
        if saved:
            logger.info("Saved seen jobs to database")
            return
    except Exception as e:
        logger.error("Database save_seen_jobs failed; fallback to local files: %s", e)

    SEEN_DIR.mkdir(parents=True, exist_ok=True)
    for country, items in added_by_country.items():
        if not items:
            continue
        path = _country_file(country)
        existing = (
            [line.strip() for line in path.read_text().splitlines() if line.strip()]
            if path.exists()
            else []
        )
        seen = set(existing)
        for item in items:
            if isinstance(item, dict):
                jid = str(item.get("job_id") or "").strip()
            else:
                jid = str(item).strip()
            if jid and jid not in seen:
                existing.append(jid)
                seen.add(jid)
        if len(existing) > MAX_SEEN:
            existing = existing[-MAX_SEEN:]
        path.write_text("\n".join(existing))


def get_seen_job_ids_for_candidates(job_ids):
    """Alias with explicit naming for job-id based dedupe."""
    return get_seen_urls_for_candidates(job_ids)
