import streamlit as st
import requests
import json
from groq import Groq

st.set_page_config(page_title="Signal — Internship Matching Agent", page_icon="◎", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: #F6F2E9;
}

.signal-header {
    padding: 0.5rem 0 1.5rem 0;
    border-bottom: 1px solid rgba(29, 44, 78, 0.15);
    margin-bottom: 1.75rem;
}
.signal-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    color: #B5792A;
    letter-spacing: 0.18em;
    font-size: 0.72rem;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.signal-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.3rem;
    color: #1D2C4E;
    margin: 0;
    letter-spacing: -0.02em;
}
.signal-sub {
    color: #5B5647;
    font-size: 0.98rem;
    margin-top: 0.5rem;
    max-width: 34rem;
}

div[data-testid="stForm"] {
    background: #FFFDF8;
    border: 1px solid rgba(29, 44, 78, 0.14);
    border-radius: 14px;
    padding: 1.6rem 1.6rem 1rem 1.6rem;
}

.stTextInput input, .stTextArea textarea {
    background: #FBF8F1 !important;
    border: 1px solid rgba(29, 44, 78, 0.18) !important;
    border-radius: 8px !important;
    color: #1D2C4E !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #1D2C4E !important;
    box-shadow: 0 0 0 1px #1D2C4E !important;
}

.stFormSubmitButton button {
    background: #1D2C4E !important;
    color: #F6F2E9 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.55rem 1.4rem !important;
}
.stFormSubmitButton button:hover {
    background: #2A3D68 !important;
}

.match-card {
    position: relative;
    background: #FFFDF8;
    border: 1px solid rgba(29, 44, 78, 0.12);
    border-left: 3px solid #1D2C4E;
    border-radius: 10px;
    padding: 1.3rem 1.5rem 1.4rem 1.5rem;
    margin-bottom: 1.1rem;
}
.match-rank {
    font-family: 'JetBrains Mono', monospace;
    color: #B5792A;
    font-size: 0.78rem;
    letter-spacing: 0.1em;
}
.match-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    color: #1D2C4E;
    margin: 0.15rem 0 0.35rem 0;
}
.match-meta {
    color: #6B6656;
    font-size: 0.9rem;
    margin-bottom: 0.9rem;
}
.match-score {
    font-family: 'JetBrains Mono', monospace;
    color: #B5792A;
    background: rgba(181, 121, 42, 0.12);
    border-radius: 4px;
    padding: 0.05rem 0.4rem;
}
.pitch-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #B5792A;
    margin-bottom: 0.35rem;
}
.pitch-text {
    color: #33302A;
    font-size: 0.95rem;
    line-height: 1.55;
}
</style>

<div class="signal-header">
    <div class="signal-eyebrow">◎ AUTONOMOUS AGENT · LIVE INTERNSHIP DATA</div>
    <div class="signal-title">Signal</div>
    <div class="signal-sub">Searches real listings, scores them against your skills, and drafts a tailored pitch for the strongest matches — no hardcoded steps, the agent decides its own path.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Fraunces', serif !important; letter-spacing: -0.01em; }

.stApp { background: #FAF8F5; }

/* Pipeline signature strip */
.pipeline-strip {
    display: flex; align-items: center; gap: 0.6rem;
    margin: 0.4rem 0 1.6rem 0; flex-wrap: wrap;
}
.pipeline-step {
    background: #FFFFFF; border: 1px solid #E4DFD6; border-radius: 999px;
    padding: 0.35rem 0.9rem; font-size: 0.82rem; font-weight: 600;
    color: #1E3A5F; display: flex; align-items: center; gap: 0.4rem;
}
.pipeline-arrow { color: #C9A15A; font-size: 1rem; }

/* Result cards */
.result-card {
    background: #FFFFFF; border: 1px solid #E9E4DA; border-radius: 14px;
    padding: 1.4rem 1.6rem; margin-bottom: 1.1rem;
    box-shadow: 0 1px 3px rgba(30,58,95,0.05);
}
.result-card h3 { margin: 0 0 0.3rem 0; color: #1E3A5F; font-size: 1.35rem; }
.result-meta { color: #6B7280; font-size: 0.92rem; margin-bottom: 0.8rem; }
.match-badge {
    display: inline-block; background: #F0E6D2; color: #8A6A1F;
    border-radius: 999px; padding: 0.15rem 0.65rem; font-size: 0.78rem;
    font-weight: 600; margin-left: 0.4rem;
}
.pitch-label {
    font-weight: 600; color: #1E3A5F; font-size: 0.85rem;
    text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.3rem;
}
.pitch-text { color: #2C2C2C; line-height: 1.55; margin-bottom: 0.9rem; }

div[data-testid="stForm"] {
    background: #FFFFFF; border: 1px solid #E9E4DA; border-radius: 16px;
    padding: 1.6rem;
}
.stButton button, .stFormSubmitButton button {
    background: #1E3A5F !important; color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
}
div[data-testid="stLinkButton"] a {
    background: #FFFFFF !important; color: #1E3A5F !important;
    border: 1.5px solid #1E3A5F !important; border-radius: 8px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Secrets & client ----------------
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


# ---------------- Tools ----------------
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


# ---------------- Agent loop (collects structured results for the UI) ----------------
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


# ---------------- UI ----------------
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

        pitch_by_title = {p["listing_title"]: p["pitch"] for p in pitches}

        if not listings:
            st.info("No matching listings found — try a broader field or fewer skill keywords.")
        else:
            st.markdown('<div class="signal-eyebrow" style="margin-top:1.5rem;">RANKED RESULTS</div>', unsafe_allow_html=True)
            for i, job in enumerate(listings[:5], start=1):
                pitch_html = ""
                if job['title'] in pitch_by_title:
                    pitch_text = pitch_by_title[job['title']]
                    pitch_html = (
                        '<div class="pitch-label">Pitch</div>'
                        f'<div class="pitch-text">{pitch_text}</div>'
                    )
                card_html = (
                    '<div class="match-card">'
                    f'<div class="match-rank">{i:02d}</div>'
                    f'<div class="match-title">{job["title"]}</div>'
                    f'<div class="match-meta">{job["company"]} · {job["location"]} · '
                    f'<span class="match-score">score {job["match_score"]}</span></div>'
                    f'{pitch_html}'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
                if job.get("url"):
                    st.link_button("Apply / View Listing", job["url"])
