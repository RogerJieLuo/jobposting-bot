from pathlib import Path

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


def save_seen_jobs(added_by_country: dict[str, list[str]]):
    """
    Persist seen job IDs per country. added_by_country: country_key -> list of job IDs added this run.
    """
    if not added_by_country:
        return
    SEEN_DIR.mkdir(parents=True, exist_ok=True)
    for country, new_ids in added_by_country.items():
        if not new_ids:
            continue
        path = _country_file(country)
        existing = (
            [line.strip() for line in path.read_text().splitlines() if line.strip()]
            if path.exists()
            else []
        )
        seen = set(existing)
        for jid in new_ids:
            if jid and jid not in seen:
                existing.append(jid)
                seen.add(jid)
        if len(existing) > MAX_SEEN:
            existing = existing[-MAX_SEEN:]
        path.write_text("\n".join(existing))
