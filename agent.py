"""
agent.py — The decide -> act -> observe -> repeat loop.
This is hand-built tool-calling against the Groq API directly —
no LangChain, no agent framework. The loop logic is fully visible here.
"""
import json
import time
import re
import groq
from config import client, MODEL
from tools import TOOL_FUNCTIONS, tool_schemas

SYSTEM_PROMPT = (
    "You are an assistant that uses tools step by step. "
    "Call only ONE tool at a time. Never nest a tool call inside another "
    "tool's arguments. Wait for a tool's result before deciding the next step. "
    "You must NEVER write pitch or cover-letter text directly in your own reply. "
    "Any pitch content MUST come from calling the draft_pitch tool — even though "
    "you are capable of writing it yourself, you are required to use the tool "
    "so the output follows the exact required format. "
    "score_match takes no arguments — call it with an empty object. "
    "draft_pitch only needs the zero-based listing_index — never repeat listing "
    "title, company, or description back as arguments."
)

MAX_LOOPS = 8  # safety cap so a stuck loop can't run forever


def call_groq_with_retry(messages, max_retries=5):
    """
    Wraps the Groq chat completion call with exponential backoff on rate limits.
    Parses Groq's "try again in Xs" message when present and waits that long
    instead of guessing.
    """
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=MODEL, messages=messages, tools=tool_schemas, tool_choice="auto",
            )
        except groq.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            match = re.search(r"try again in ([\d.]+)s", str(e))
            wait_time = float(match.group(1)) + 0.5 if match else (2 ** attempt) + 1
            print(f"Rate limited. Retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)


def run_agent(user_goal: str, skills: list, projects: list, status_box=None):
    """
    Runs the full agent loop. Returns (scored_listings, pitches, final_text).
    status_box is an optional Streamlit st.status() object for live UI updates.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{user_goal}\nMy skills: {', '.join(skills)}\nMy projects: {', '.join(projects)}"}
    ]
    raw_listings = []        # accumulated across search_internships calls
    collected_listings = []  # scored + sorted, set by score_match
    collected_pitches = []
    loop_count = 0

    while loop_count < MAX_LOOPS:
        loop_count += 1
        response = call_groq_with_retry(messages)
        message = response.choices[0].message
        tool_calls = message.tool_calls

        if tool_calls:
            messages.append(message)
            for call in tool_calls:
                fn_name = call.function.name
                fn_args = json.loads(call.function.arguments) if call.function.arguments else {}

                if status_box:
                    if fn_name == "search_internships":
                        status_box.write(f"🔍 Searching: *{fn_args.get('query')}*")
                    elif fn_name == "score_match":
                        status_box.write("📊 Scoring listings against your skills...")
                    elif fn_name == "draft_pitch":
                        status_box.write("✍️ Drafting pitch...")

                # score_match and draft_pitch get their real arguments built
                # here from what the agent already holds in Python, instead
                # of trusting the model to repeat full listing data back as
                # function-call arguments. That duplication — once in the
                # tool result, again in the model's own arguments — was
                # driving the TPM rate limit.
                if fn_name == "search_internships":
                    result = TOOL_FUNCTIONS[fn_name](**fn_args)
                    raw_listings.extend(result)
                    tool_result_for_model = {"status": "found", "count": len(result)}

                elif fn_name == "score_match":
                    result = TOOL_FUNCTIONS[fn_name](listings=raw_listings, skills=skills)
                    collected_listings = result
                    tool_result_for_model = {"status": "scored", "count": len(result)}

                elif fn_name == "draft_pitch":
                    idx = fn_args.get("listing_index", 0)
                    if not isinstance(idx, int) or idx < 0 or idx >= len(collected_listings):
                        tool_result_for_model = {"status": "error", "message": "invalid listing_index"}
                    else:
                        listing = collected_listings[idx]
                        result = TOOL_FUNCTIONS[fn_name](listing=listing, skills=skills, projects=projects)
                        collected_pitches.append(result)
                        tool_result_for_model = {"status": "pitch_drafted"}

                else:
                    result = TOOL_FUNCTIONS[fn_name](**fn_args)
                    tool_result_for_model = result

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_result_for_model)
                })
        else:
            return collected_listings, collected_pitches, message.content

    return collected_listings, collected_pitches, "Reached the loop limit — try a narrower search."
