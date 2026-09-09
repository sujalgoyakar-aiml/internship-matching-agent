"""
agent.py — The decide -> act -> observe -> repeat loop.
Hand-built tool-calling against Groq API directly.
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
    "so the output follows the exact required format."
)

MAX_LOOPS = 8


def call_groq_with_retry(messages, max_retries=5):
    """Handles rate-limiting gracefully with automatic backoff retries."""
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto",
            )
        except groq.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            match = re.search(r"try again in ([\d.]+)s", str(e))
            wait_time = float(match.group(1)) + 0.5 if match else (2 ** attempt) + 1
            time.sleep(wait_time)


def run_agent(user_goal: str, skills: list, projects: list, status_box=None):
    """
    Runs the full agent loop safely without crashing on missing tool parameters.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{user_goal}\nMy skills: {', '.join(skills)}\nMy projects: {', '.join(projects)}"}
    ]
    raw_listings = []
    collected_listings = []
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

                # Safe Status UI Update
                if status_box:
                    if fn_name == "search_internships":
                        status_box.write(f"🔍 Searching: *{fn_args.get('query', 'internships')}*")
                    elif fn_name == "score_match":
                        status_box.write("📊 Scoring listings against your skills...")
                    elif fn_name == "draft_pitch":
                        status_box.write("✍️ Drafting pitch...")

                # Tool Execution Logic
                if fn_name == "search_internships":
                    query = fn_args.get("query", "internship")
                    raw_listings = TOOL_FUNCTIONS[fn_name](query=query)
                    tool_result_for_model = raw_listings

                elif fn_name == "score_match":
                    listings_to_score = fn_args.get("listings") or raw_listings
                    collected_listings = TOOL_FUNCTIONS[fn_name](listings=listings_to_score, skills=skills)
                    tool_result_for_model = collected_listings

                elif fn_name == "draft_pitch":
                    # Retrieve target listing safely
                    target_listing = fn_args.get("listing")
                    if not target_listing and collected_listings:
                        target_listing = collected_listings[0]

                    if target_listing:
                        pitch_res = TOOL_FUNCTIONS[fn_name](
                            listing=target_listing,
                            skills=skills,
                            projects=projects
                        )
                        collected_pitches.append(pitch_res)
                        tool_result_for_model = pitch_res
                    else:
                        tool_result_for_model = {"error": "No valid listing available to draft pitch."}

                else:
                    func = TOOL_FUNCTIONS[fn_name]
                    tool_result_for_model = func(**fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_result_for_model)
                })
        else:
            return collected_listings, collected_pitches, message.content

    return collected_listings, collected_pitches, "Reached loop limit."
