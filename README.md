# Signal — Internship Matching Agent

An autonomous AI agent that searches real internship listings, scores them
against a candidate's skills, and drafts tailored application pitches —
built on a hand-written **decide → act → observe → repeat** tool-calling
loop against the raw Groq API. No agent framework (no LangChain, no
CrewAI) — the loop logic is fully visible and hand-built.

*Live demo:* https://internship-matching-agent-4sqz4bwmacubdh84frxhk8.streamlit.app

# Project structure

```
app.py       — UI layer (Streamlit forms, result cards)
agent.py     — the decide/act/observe/repeat loop
tools.py     — the 3 tools + their schemas
db.py        — Supabase persistence (profile, search history, applications)
config.py    — secrets and client setup
styles.py    — CSS, isolated from layout logic
```

Each file has one job. `agent.py` never touches Streamlit; `app.py` never
touches the Groq or Adzuna APIs directly; `db.py` degrades gracefully
(silently disables) if Supabase isn't configured.

# How it works

1. **`search_internships`** — queries the [Adzuna](https://developer.adzuna.com) jobs API for real, current listings in any field
2. **`score_match`** — ranks listings by keyword overlap with the candidate's stated skills
3. **`draft_pitch`** — generates a short, tailored 3-sentence pitch per top listing via an internal LLM call

The model (via [Groq](https://groq.com), `openai/gpt-oss-120b`) decides
which tool to call and when — including retrying with a broader search
query if an initial search returns nothing.

# Persistence

Profile (skills/projects), search history, and marked applications are
stored in a [Supabase](https://supabase.com) Postgres database — see
`signal_supabase_setup.sql` for the schema.

# Run locally

```bash
git clone <this-repo>
cd signal-app
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_groq_key"
ADZUNA_APP_ID = "your_adzuna_app_id"
ADZUNA_APP_KEY = "your_adzuna_app_key"
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_KEY = "your_supabase_anon_key"
```

```bash
streamlit run app.py
```

# Tech stack

Python · Groq API (LLM + tool calling, hand-built loop) · Adzuna API (real job data) · Supabase (persistence) · Streamlit
