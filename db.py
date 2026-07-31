"""
db.py — All Supabase persistence logic lives here, isolated from the UI
and the agent. If Supabase isn't configured (SUPABASE_ENABLED is False),
every function here becomes a safe no-op instead of crashing the app.
"""

from config import supabase, SUPABASE_ENABLED


def load_profile():
    """Returns the saved (skills, projects, field) or (None, None, None)."""
    if not SUPABASE_ENABLED:
        return None, None, None
    result = supabase.table("profile").select("*").order("updated_at", desc=True).limit(1).execute()
    if result.data:
        row = result.data[0]
        return row.get("field"), row.get("skills"), row.get("projects")
    return None, None, None


def save_profile(field: str, skills: str, projects: str):
    """Upserts the single profile row (this is a personal single-user tool)."""
    if not SUPABASE_ENABLED:
        return
    supabase.table("profile").insert({
        "field": field, "skills": skills, "projects": projects,
    }).execute()


def log_search(field: str, skills: str, projects: str):
    if not SUPABASE_ENABLED:
        return
    supabase.table("search_history").insert({
        "field": field, "skills": skills, "projects": projects,
    }).execute()


def mark_applied(title: str, company: str, url: str):
    if not SUPABASE_ENABLED:
        return
    supabase.table("applications").insert({
        "title": title, "company": company, "url": url, "status": "applied",
    }).execute()


def get_applied_urls():
    """Returns a set of URLs already marked applied, so the UI can flag them."""
    if not SUPABASE_ENABLED:
        return set()
    result = supabase.table("applications").select("url").execute()
    return {row["url"] for row in result.data}


def get_search_history(limit: int = 10):
    if not SUPABASE_ENABLED:
        return []
    result = supabase.table("search_history").select("*").order("created_at", desc=True).limit(limit).execute()
    return result.data
