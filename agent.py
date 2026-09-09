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

# Cap on how many listings we ever echo back into the model's context,
# and how long any single text field can be before we truncate it.
MAX_LISTINGS_IN_CONTEXT = 8
MAX_FIELD_CHARS = 300


def _truncate_text(value, limit=MAX_FIELD_CHARS):
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "...[truncated]"
    return value


def _slim_listing(listing: dict) -> dict:
    """
    Keep only what the model needs to reason about a listing —
    drop huge raw fields (full descriptions, HTML, etc.) and
    truncate whatever text fields remain.
    Adjust the 'keep' keys once you share tools.py's actual listing schema.
    """
    if not isinstance(listing, dict):
        return listing
    keep = ["id", "title", "company", "location", "url", "description", "score"]
    slim = {k: _truncate_text(listing[k]) for k in keep if k in listing}
    return slim


def _slim_for_model(fn_name: str, result):
    """
    Produces a compact version of a tool's result to store in `messages`,
    so conversation history doesn't balloon across loop iterations.
    The FULL result still stays in Python (raw_listings / collected_listings /
    collected_pitches) — only what goes back to the model gets slimmed.
    """
    if fn_name in ("search_internships", "score_match"):
        if isinstance(result, list):
            slimmed = [_slim_listing(item) for item in result[:MAX_LISTINGS_IN_CONTEXT]]
            if len(result) > MAX_LISTINGS_IN_CONTEXT:
                return {
                    "listings": slimmed,
                    "note": f"{len(result) - MAX_LISTINGS_IN_CONTEXT} more listings omitted for brevity."
                }
            return slimmed
        return result

    if fn_name == "draft_pitch":
        if isinstance(result, dict):
            return {
                "status": "pitch_drafted",
                "listing_title": result.get("listing_title") or result.get("title"),
                "preview": _truncate_text(str(result.get("pitch") or result.get("content") or result), 200),
            }
        return {"status": "pitch_drafted"}

    return result


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

                # Tool Execution Logic — full, untrimmed results kept here in Python
                if fn_name == "search_internships":
                    query = fn_args.get("query", "internship")
                    raw_listings = TOOL_FUNCTIONS[fn_name](query=query)
                    tool_result_for_model = raw_listings

                elif fn_name == "score_match":
                    listings_to_score = fn_args.get("listings") or raw_listings
                    collected_listings = TOOL_FUNCTIONS[fn_name](listings=listings_to_score, skills=skills)
                    tool_result_for_model = collected_listings

                elif fn_name == "draft_pitch":
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

                # Only the SLIMMED version goes back into conversation history —
                # this is what stops messages from ballooning across loop iterations.
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(_slim_for_model(fn_name, tool_result_for_model))
                })
        else:
            return collected_listings, collected_pitches, message.content

    return collected_listings, collected_pitches, "Reached loop limit."
