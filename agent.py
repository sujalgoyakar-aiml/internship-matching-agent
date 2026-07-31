"""
agent.py — The decide -> act -> observe -> repeat loop.
This is hand-built tool-calling against the Groq API directly —
no LangChain, no agent framework. The loop logic is fully visible here.
"""

import json
from config import client, MODEL
from tools import TOOL_FUNCTIONS, tool_schemas

SYSTEM_PROMPT = (
    "You are an assistant that uses tools step by step. "
    "Call only ONE tool at a time. Never nest a tool call inside another "
    "tool's arguments. Wait for a tool's result before deciding the next step. "
    "You must NEVER write pitch or cover-letter text directly in your own reply. "
    "Any pitch content MUST come from calling the draft_pitch tool — even though "
    "you are capable of writing it yourself, you are required to use the tool "
    "so the output follows the exact required format."
)

MAX_LOOPS = 8  # safety cap so a stuck loop can't run forever


def run_agent(user_goal: str, skills: list, projects: list, status_box=None):
    """
    Runs the full agent loop. Returns (scored_listings, pitches, final_text).
    status_box is an optional Streamlit st.status() object for live UI updates.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{user_goal}\nMy skills: {', '.join(skills)}\nMy projects: {', '.join(projects)}"}
    ]

    collected_listings = []
    collected_pitches = []

    loop_count = 0
    while loop_count < MAX_LOOPS:
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

                if status_box:
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
