"""
config.py — Loads all secrets and creates all external clients.
Nothing else in the app should touch st.secrets directly.
"""

import streamlit as st
from groq import Groq
from supabase import create_client

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
ADZUNA_APP_ID = st.secrets["ADZUNA_APP_ID"]
ADZUNA_APP_KEY = st.secrets["ADZUNA_APP_KEY"]

MODEL = "openai/gpt-oss-120b"
client = Groq(api_key=GROQ_API_KEY)

# Supabase is optional — if not configured yet, persistence features
# quietly disable instead of crashing the whole app.
SUPABASE_ENABLED = "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets

supabase = None
if SUPABASE_ENABLED:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
