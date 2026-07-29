import streamlit as st
import requests
import json
from groq import Groq

st.set_page_config(page_title="Internship Matching Agent", page_icon="🎯", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
ADZUNA_APP_ID = st.secrets["ADZUNA_APP_ID"]
ADZUNA_APP_KEY = st.secrets["ADZUNA_APP_KEY"]

client = Groq(api_key=GROQ_API_KEY)
MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are an assistant that uses tools step by step. "
    "Call only ONE tool at a time. Never nest a tool call inside another "
    "tool's arguments. Wait for a tool's result before deciding the next step. "
    "You must NEVER write pitch or cover-letter text directly in your own reply. "
    "Any pitch content MUST come from calling the draft_pitch tool — even though "
    "you are capable of writing it yourself, you are required to use the tool "
    "so the output follows the exact required format."
)


def search_internships(query: str):
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY, "results_per_page": 10,
        "what": query, "content-type": "application/json",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    raw_results = data.get("results", [])
    listings = []
    for job in raw_results:
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
        overlap = sum(1 for s in skills if s.lower() in job["desc"].lower())
        scored.append({**job, "match_score": overlap})
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


def draft_pitch(listing: dict, skills: list, projects: list):
    if isinstance(projects, str):
        projects = [projects]
    if isinstance(skills, str):
        skills = [skills]
    prompt = f"""Write a short, genuine-sounding 3-sentence pitch for this internship application.

Internship: {listing.get('title')} at {listing.get('company')}
Internship description: {listing.get('desc')}

Candidate skills: {', '.join(skills)}
Candidate projects: {', '.join(projects)}

Rules:
- Reference ONE specific project that matches what this internship is asking for
- Mirror the internship's own language/keywords where relevant
- Keep it to 3 sentences, no fluff, no generic phrases like "I am passionate about"
- Do not use placeholders like [Company Name] - use the real company name given above
"""
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=500,
    )
    pitch_text = response.choices[0].message.content
    return {"listing_title": listing.get("title"), "company": listing.get("company"), "pitch": pitch_text}


TOOL_FUNCTIONS = {
    "search_internships": search_internships,
    "score_match": score_match,
    "draft_pitch": draft_pitch,
}

tool_schemas = [
    {"type": "function", "function": {
        "name": "search_internships",
        "description": "Search internship platforms for listings matching a query.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Search query, e.g. 'AI ML internship Pune'"}},
            "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "score_match",
        "description": "Score a list of internship listings against a list of candidate skills.",
        "parameters": {"type": "object", "properties": {
            "listings": {"type": "array", "description": "List of internship listing objects to score"},
            "skills": {"type": "array", "items": {"type": "string"}, "description": "Candidate's skill list"}},
            "required": ["listings", "skills"]},
    }},
    {"type": "function", "function": {
        "name": "draft_pitch",
        "description": "Generate a short tailored pitch for ONE specific internship listing, referencing the candidate's matching project and skills.",
        "parameters": {"type": "object", "properties": {
            "listing": {"type": "object", "description": "A single internship listing object (title, company, desc)"},
            "skills": {"type": "array", "items": {"type": "string"}, "description": "Candidate's skill list"},
            "projects": {"type": "array", "items": {"type": "string"}, "description": "Candidate's project names/descriptions"}},
            "required": ["listing", "skills", "projects"]},
    }},
]


def run_agent(user_goal: str, skills: list, projects: list, status_box):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{user_goal}\nMy skills: {', '.join(skills)}\nMy projects: {', '.join(projects)}"}
    ]

    collected_listings = []
    collected_pitches = []

    loop_count = 0
    max_loops = 8  # safety cap so a stuck loop can't run forever
    while loop_count < max_loops:
        loop_count += 1
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tool_schemas, tool_choice="auto",
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls

        if tool_calls:
            messages.append(message)
            for call in tool_calls:
                fn_name = call.function.name
                fn_args = json.loads(call.function.arguments)

                if fn_name == "search_internships":
                    status_box.write(f"🔍 Searching: *{fn_args.get('query')}*")
                elif fn_name == "score_match":
                    status_box.write("📊 Scoring listings against your skills...")
                elif fn_name == "draft_pitch":
                    status_box.write(f"✍️ Drafting pitch for **{fn_args.get('listing', {}).get('title', '')}**...")

                func = TOOL_FUNCTIONS[fn_name]
                result = func(**fn_args)

                if fn_name == "score_match":
                    collected_listings = result
                if fn_name == "draft_pitch":
                    collected_pitches.append(result)

                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
        else:
            return collected_listings, collected_pitches, message.content

    return collected_listings, collected_pitches, "Reached the loop limit — try a narrower search."


st.title("🎯 Internship Matching Agent")
st.caption("Finds real internships, scores them against your skills, and drafts a tailored pitch for the best matches.")

with st.form("search_form"):
    field = st.text_input("Field / Department", placeholder="e.g. AI/ML, Civil, Mechanical, MBBS")
    skills_input = st.text_input("Your skills (comma-separated)", placeholder="e.g. Python, RAG, Streamlit")
    projects_input = st.text_area("Your projects/experience (comma-separated)",
                                   placeholder="e.g. StudyMate AI - RAG-based study assistant using Groq API")
    submitted = st.form_submit_button("Find Internships & Draft Pitches")

if submitted:
    if not field or not skills_input or not projects_input:
        st.warning("Please fill in all three fields.")
    else:
        skills = [s.strip() for s in skills_input.split(",") if s.strip()]
        projects = [p.strip() for p in projects_input.split(",") if p.strip()]

        with st.status("Agent working...", expanded=True) as status_box:
            listings, pitches, final_text = run_agent(
                user_goal=f"Find {field} internships that match my skills, rank them, and draft a pitch for the top 2.",
                skills=skills, projects=projects, status_box=status_box,
            )
            status_box.update(label="Done", state="complete")

        st.divider()

        pitch_by_title = {p["listing_title"]: p["pitch"] for p in pitches}

        if not listings:
            st.info("No matching listings found — try a broader field or fewer skill keywords.")
        else:
            st.subheader("Top Matches")
            for job in listings[:5]:
                with st.container(border=True):
                    st.markdown(f"### {job['title']}")
                    st.markdown(f"**{job['company']}** · {job['location']} · Match score: {job['match_score']}")
                    if job['title'] in pitch_by_title:
                        st.markdown("**Pitch:**")
                        st.write(pitch_by_title[job['title']])
                    if job.get("url"):
                        st.link_button("Apply / View Listing", job["url"])
