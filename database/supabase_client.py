import os
from supabase import create_client
from utils.config_loader import load_supabase_service_role_key, load_supabase_url
from utils.logger import logger


def get_supabase_table_name() -> str:
    return os.getenv("SUPABASE_SEEN_JOBS_TABLE", "seen_jobs").strip() or "seen_jobs"


def get_supabase_client():
    try:
        url = (load_supabase_url() or "").strip()
        key = (load_supabase_service_role_key() or "").strip()
    except Exception:
        return None
    if not url or not key:
        return None
    
    try:
        return create_client(url, key)
    except Exception as e:
        logger.error("Failed creating Supabase client: %s", e)
        return None
