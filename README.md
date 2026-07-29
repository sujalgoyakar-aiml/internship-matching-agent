# Internship Matching Agent

An autonomous AI agent that searches real internship listings, scores them
against a candidate's skills, and drafts tailored application pitches —
built on a **decide → act → observe → repeat** tool-calling loop, wrapped
in a clean Streamlit interface.

**Live demo:** _add your Streamlit Cloud link here after deploying_

## How it works

The agent has three tools, and decides on its own which to call and when —
there is no hardcoded sequence:

1. **`search_internships`** — queries the [Adzuna](https://developer.adzuna.com) jobs API for real, current listings in any field (not limited to tech)
2. **`score_match`** — ranks listings by keyword overlap with the candidate's stated skills
3. **`draft_pitch`** — generates a short, tailored 3-sentence pitch per top listing via an internal LLM call, referencing one specific matching project

The model (via [Groq](https://groq.com), running `openai/gpt-oss-120b`) observes
each tool's real output and decides the next step itself — including
retrying with a broader search query if an initial search returns nothing.

# Why each tool exists

- `search_internships` is a tool because the model has no internet access on its own
- `score_match` is a tool because it's a deterministic computation, not a judgment call
- `draft_pitch` is *routed through* a tool even though the model could write text
  directly — this enforces a consistent 3-sentence, placeholder-free format that
  the model does not reliably follow if left to answer freely

# Run locally

```bash
git clone <this-repo>
cd internship-agent
pip install -r requirements.txt
```

Create a file at `.streamlit/secrets.toml` with:
```toml
GROQ_API_KEY = "your_groq_key"
ADZUNA_APP_ID = "your_adzuna_app_id"
ADZUNA_APP_KEY = "your_adzuna_app_key"
```

Then run:
```bash
streamlit run app.py
```

# Tech stack

Python · Groq API (LLM + tool calling) · Adzuna API (real job data) · Streamlit
