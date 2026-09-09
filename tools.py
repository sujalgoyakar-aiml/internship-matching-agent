import requests
from config import client, MODEL, ADZUNA_APP_ID, ADZUNA_APP_KEY


def search_internships(query: str):
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 10,
        "what": query,
        "content-type": "application/json",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []

    data = response.json()
    listings = []
    for job in data.get("results", []):
        listings.append({
            "title": job.get("title", "Unknown title"),
            "company": job.get("company", {}).get("display_name", "Unknown company"),
            "location": job.get("location", {}).get("display_name", "Unknown location"),
            "desc": job.get("description", "")[:300],
            "url": job.get("redirect_url", ""),
        })
    return listings


def score_match(listings: list, skills: list):
    scored = []
    for job in listings:
        overlap = sum(1 for s in skills if s.lower() in job.get("desc", "").lower())
        scored.append({**job, "match_score": overlap})
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


def draft_pitch(listing: dict, skills: list, projects: list):
    if isinstance(projects, str):
        projects = [projects]
    if isinstance(skills, str):
        skills = [skills]

    prompt = f"""Write a short, genuine-sounding 3-sentence pitch for this internship application.

Internship: {listing.get('title', 'Position')} at {listing.get('company', 'Company')}
Internship description: {listing.get('desc', '')}

Candidate skills: {', '.join(skills)}
Candidate projects: {', '.join(projects)}

Rules:
- Reference ONE specific project that matches what this internship is asking for
- Mirror the internship's own language/keywords where relevant
- Keep it to 3 sentences, no fluff, no generic phrases like "I am passionate about"
- Do not use placeholders like [Company Name] - use the real company name given above
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    pitch_text = response.choices[0].message.content
    return {"listing_title": listing.get("title"), "company": listing.get("company"), "pitch": pitch_text}


TOOL_FUNCTIONS = {
    "search_internships": search_internships,
    "score_match": score_match,
    "draft_pitch": draft_pitch,
}

tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "search_internships",
            "description": "Search internship platforms for listings matching a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query, e.g. 'AI ML internship Pune'"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_match",
            "description": "Score a list of internship listings against a list of candidate skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "listings": {"type": "array", "description": "List of internship listing objects to score"},
                    "skills": {"type": "array", "items": {"type": "string"}, "description": "Candidate's skill list"},
                },
                "required": ["listings", "skills"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_pitch",
            "description": "Generate a short tailored pitch for ONE specific internship listing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing": {"type": "object", "description": "A single internship listing object (title, company, desc)"},
                    "skills": {"type": "array", "items": {"type": "string"}, "description": "Candidate's skill list"},
                    "projects": {"type": "array", "items": {"type": "string"}, "description": "Candidate's project list"},
                },
                "required": ["listing"],
            },
        },
    },
]
