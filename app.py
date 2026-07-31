"""
app.py — UI layer only. All logic lives in agent.py, tools.py, db.py.
Run locally with: streamlit run app.py
"""

import streamlit as st
from agent import run_agent
from db import load_profile, save_profile, log_search, mark_applied, get_applied_urls
from styles import SIGNAL_CSS, SIGNAL_HEADER

st.set_page_config(page_title="Signal — Internship Matching Agent", page_icon="◎", layout="centered")
st.markdown(SIGNAL_CSS, unsafe_allow_html=True)
st.markdown(SIGNAL_HEADER, unsafe_allow_html=True)

# Auto-fill from last saved profile, if one exists
saved_field, saved_skills, saved_projects = load_profile()

with st.form("search_form"):
    field = st.text_input("Field / Department — e.g. AI/ML, Civil, Mechanical, MBBS",
                           value=saved_field or "")
    st.caption("What area are you looking for internships in?")

    skills_input = st.text_input("Your skills, comma-separated — e.g. Python, RAG, Streamlit",
                                  value=saved_skills or "")
    st.caption("List your technical or subject skills, separated by commas.")

    projects_input = st.text_area("Your projects/experience, comma-separated — e.g. StudyMate AI: RAG-based study assistant",
                                   value=saved_projects or "")
    st.caption("Briefly describe your projects or work experience — this is what the pitch will reference.")

    submitted = st.form_submit_button("Find Internships & Draft Pitches")

if submitted:
    if not field or not skills_input or not projects_input:
        st.warning("Please fill in all three fields.")
    else:
        skills = [s.strip() for s in skills_input.split(",") if s.strip()]
        projects = [p.strip() for p in projects_input.split(",") if p.strip()]

        save_profile(field, skills_input, projects_input)
        log_search(field, skills_input, projects_input)

        with st.status("Agent working...", expanded=True) as status_box:
            listings, pitches, final_text = run_agent(
                user_goal=f"Find {field} internships that match my skills, rank them, and draft a pitch for the top 2.",
                skills=skills, projects=projects, status_box=status_box,
            )
            status_box.update(label="Done", state="complete")

        pitch_by_title = {p["listing_title"]: p["pitch"] for p in pitches}
        applied_urls = get_applied_urls()

        if not listings:
            st.info("No matching listings found — try a broader field or fewer skill keywords.")
        else:
            st.markdown('<div class="signal-eyebrow" style="margin-top:1.5rem;">RANKED RESULTS</div>', unsafe_allow_html=True)
            for i, job in enumerate(listings[:5], start=1):
                already_applied = job.get("url") in applied_urls
                applied_html = '<span class="applied-badge">✓ applied</span>' if already_applied else ""

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
                    f'<span class="match-score">score {job["match_score"]}</span>{applied_html}</div>'
                    f'{pitch_html}'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                with col1:
                    if job.get("url"):
                        st.link_button("Apply / View Listing", job["url"])
                with col2:
                    if not already_applied and job.get("url"):
                        if st.button("Mark as Applied", key=f"apply_{i}"):
                            mark_applied(job["title"], job["company"], job["url"])
                            st.rerun()
