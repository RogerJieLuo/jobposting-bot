from datetime import datetime, timezone

from database.supabase_client import get_supabase_client, get_supabase_table_name


def _normalize_row(item):
    if isinstance(item, str):
        return {"job_id": item}
    if not isinstance(item, dict):
        return None
    job_id = str(item.get("job_id") or "").strip()
    if not job_id:
        return None
    url = (item.get("url") or "").strip()
    return {
        "job_id": job_id,
        "url": url or None,
        "job_title": item.get("job_title"),
        "company": item.get("company"),
        "location": item.get("location"),
        "job_description": item.get("job_description"),
        "rank": item.get("rank") if isinstance(item.get("rank"), dict) else None,
        "update_at": datetime.now(timezone.utc).isoformat(),
    }


def load_seen_jobs():
    client = get_supabase_client()
    if client is None:
        return None
    table = get_supabase_table_name()
    result = {}
    seen_urls = set()
    page = 1000
    offset = 0
    while True:
        resp = client.table(table).select("job_id").range(offset, offset + page - 1).execute()
        rows = resp.data or []
        if not rows:
            break
        for row in rows:
            job_id = str(row.get("job_id") or "").strip()
            if job_id:
                seen_urls.add(job_id)
        if len(rows) < page:
            break
        offset += page
    result["default"] = seen_urls
    return result


def find_existing_job_ids(job_ids, chunk_size=200):
    client = get_supabase_client()
    if client is None:
        return None
    table = get_supabase_table_name()
    candidates = [str(v).strip() for v in (job_ids or []) if str(v).strip()]
    if not candidates:
        return set()

    found = set()
    for i in range(0, len(candidates), chunk_size):
        chunk = candidates[i : i + chunk_size]
        if not chunk:
            continue
        resp = client.table(table).select("job_id").in_("job_id", chunk).execute()
        for row in resp.data or []:
            job_id = str(row.get("job_id") or "").strip()
            if job_id:
                found.add(job_id)
    return found


def save_seen_jobs(added_by_country):
    client = get_supabase_client()
    if client is None:
        return False
    table = get_supabase_table_name()
    rows = []
    for items in added_by_country.values():
        for item in items or []:
            row = _normalize_row(item)
            if row:
                rows.append(row)
    if not rows:
        return True
    client.table(table).upsert(rows, on_conflict="job_id").execute()
    return True
