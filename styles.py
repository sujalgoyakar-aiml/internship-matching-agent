"""
styles.py — All CSS for the app lives here, as a single string.
Keeps app.py focused on layout/logic, not styling.
"""

SIGNAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #F6F2E9; }

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
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] {
    color: #1D2C4E !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    opacity: 1 !important;
}
[data-testid="stCaptionContainer"] p {
    color: #6B6656 !important;
}

.stFormSubmitButton button {
    background: #1D2C4E !important;
    color: #F6F2E9 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.55rem 1.4rem !important;
}
.stFormSubmitButton button:hover { background: #2A3D68 !important; }

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
.applied-badge {
    font-family: 'JetBrains Mono', monospace;
    color: #4B7A4E;
    background: rgba(75, 122, 78, 0.12);
    border-radius: 4px;
    padding: 0.05rem 0.4rem;
    margin-left: 0.4rem;
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
"""

SIGNAL_HEADER = """
<div class="signal-header">
    <div class="signal-eyebrow">◎ AUTONOMOUS AGENT · LIVE INTERNSHIP DATA</div>
    <div class="signal-title">Signal</div>
    <div class="signal-sub">Searches real listings, scores them against your skills, and drafts a tailored pitch for the strongest matches — no hardcoded steps, the agent decides its own path.</div>
</div>
"""
