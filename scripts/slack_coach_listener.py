#!/usr/bin/env python3
"""Poll #ascent-training for user messages and route them to the ask-coach CCD skill.

Runs as a launchd job (every 60s). Checks for unprocessed human messages,
triggers a Claude Code session with training context, and posts the reply.

Architecture:
  Slack (#ascent-training) → this script polls → claude -p → reply posted to Slack
"""
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

log = logging.getLogger("slack_coach_listener")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN") or Path(
    os.path.expanduser("~/.openclaw/slack-bot-token")
).read_text().strip()
CHANNEL_ID = os.environ.get("SLACK_CHANNEL_TRAINING", "C0AQ1KJAKM0")
BOT_USER_ID = None  # Populated on first run

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Track the last processed message timestamp to avoid duplicates
STATE_FILE = PROJECT_ROOT / "logs" / ".slack_listener_last_ts"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"


def get_bot_user_id() -> str:
    """Get the bot's own user ID so we can ignore our own messages."""
    resp = requests.get(
        "https://slack.com/api/auth.test",
        headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
    )
    data = resp.json()
    if data.get("ok"):
        return data["user_id"]
    log.warning("auth.test failed: %s", data.get("error"))
    return ""


def get_last_ts() -> str:
    """Read the last processed timestamp."""
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip()
    return "0"


def save_last_ts(ts: str):
    """Persist the last processed timestamp."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(ts)


def fetch_new_messages(oldest: str) -> list[dict]:
    """Fetch messages newer than `oldest` from #ascent-training."""
    resp = requests.get(
        "https://slack.com/api/conversations.history",
        headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
        params={"channel": CHANNEL_ID, "oldest": oldest, "limit": 10},
    )
    data = resp.json()
    if not data.get("ok"):
        log.error("conversations.history failed: %s", data.get("error"))
        return []
    return data.get("messages", [])


def is_human_message(msg: dict, bot_uid: str) -> bool:
    """Return True if this is a real human message (not bot, not system)."""
    if msg.get("bot_id"):
        return False
    if msg.get("subtype"):  # channel_join, bot_message, etc.
        return False
    if msg.get("user") == bot_uid:
        return False
    return bool(msg.get("text", "").strip())


def fetch_training_context() -> str:
    """Pre-fetch training context from Supabase for the prompt."""
    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    ctx_parts = []

    try:
        # Daily coaching context
        r = requests.get(f"{SUPABASE_URL}/rest/v1/daily_coaching_context?select=*&limit=1", headers=h)
        if r.ok and r.json():
            ctx_parts.append(f"COACHING CONTEXT:\n{json.dumps(r.json()[0], indent=2)}")
    except Exception:
        pass

    try:
        # Today's planned workout
        today = time.strftime("%Y-%m-%d")
        r = requests.get(f"{SUPABASE_URL}/rest/v1/planned_workouts?scheduled_date=eq.{today}&select=session_name,status,workout_definition,adjustment_reason", headers=h)
        if r.ok and r.json():
            ctx_parts.append(f"TODAY'S PLANNED WORKOUT:\n{json.dumps(r.json()[0], indent=2)}")
        else:
            ctx_parts.append("TODAY'S PLANNED WORKOUT: None (rest day or unplanned)")
    except Exception:
        pass

    try:
        # Recent HRV
        r = requests.get(f"{SUPABASE_URL}/rest/v1/hrv?select=date,last_night_avg,status,weekly_avg&order=date.desc&limit=7", headers=h)
        if r.ok and r.json():
            ctx_parts.append(f"HRV (last 7 days):\n{json.dumps(r.json(), indent=2)}")
    except Exception:
        pass

    try:
        # Recent activities
        r = requests.get(f"{SUPABASE_URL}/rest/v1/activities?select=date,activity_type,activity_name,duration_seconds,elevation_gain,training_effect_aerobic&order=date.desc&limit=5", headers=h)
        if r.ok and r.json():
            ctx_parts.append(f"RECENT ACTIVITIES:\n{json.dumps(r.json(), indent=2)}")
    except Exception:
        pass

    return "\n\n".join(ctx_parts)


def build_coach_prompt(user_message: str) -> str:
    """Build a prompt with pre-fetched context — no tool calls needed."""
    context = fetch_training_context()
    return f"""You are the Ascent training coach. An athlete sent this message in #ascent-training:

"{user_message}"

Here is the current training context (pre-fetched from the database):

{context}

RULES:
- Answer concisely (2-4 sentences for simple questions, more detail only if needed)
- Use Slack mrkdwn format (*bold*, _italic_)
- Reference actual numbers from the data above
- Use autonomy-supportive language (no "should", "must", "need to")
- Output ONLY the reply text. No preamble, no explanation of what you did.
"""


def run_coach_session(prompt: str) -> str | None:
    """Run a Claude session with pre-fetched context. Fast: no tool calls."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--max-turns", "1", "--model", "sonnet"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        log.error("Claude session failed (rc=%d): %s", result.returncode, result.stderr[-300:])
        return None
    except subprocess.TimeoutExpired:
        log.error("Claude session timed out (60s)")
        return None
    except FileNotFoundError:
        log.error("'claude' CLI not found in PATH")
        return None


def post_reply(text: str, thread_ts: str | None = None):
    """Post a reply to #ascent-training."""
    payload: dict = {
        "channel": CHANNEL_ID,
        "text": text,
        "mrkdwn": True,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json=payload,
    )
    data = resp.json()
    if not data.get("ok"):
        log.error("Failed to post reply: %s", data.get("error"))


def main():
    global BOT_USER_ID
    BOT_USER_ID = get_bot_user_id()
    if not BOT_USER_ID:
        log.error("Could not determine bot user ID")
        sys.exit(1)

    last_ts = get_last_ts()
    messages = fetch_new_messages(last_ts)

    # Filter to human messages only, oldest first
    human_msgs = [m for m in reversed(messages) if is_human_message(m, BOT_USER_ID)]

    if not human_msgs:
        log.info("No new human messages in #ascent-training")
        return

    log.info("Found %d new human message(s)", len(human_msgs))

    for msg in human_msgs:
        user_text = msg["text"].strip()
        msg_ts = msg["ts"]
        log.info("Processing: '%s' (ts=%s)", user_text[:80], msg_ts)

        # Build prompt and run coach session
        prompt = build_coach_prompt(user_text)
        reply = run_coach_session(prompt)

        if reply:
            # Reply in thread
            post_reply(reply, thread_ts=msg_ts)
            log.info("Reply posted (thread_ts=%s)", msg_ts)
        else:
            post_reply(
                "Sorry, I couldn't process that right now. Try again in a moment.",
                thread_ts=msg_ts,
            )

        # Update last processed timestamp
        save_last_ts(msg_ts)

        # Rate limit between messages
        time.sleep(2)


if __name__ == "__main__":
    main()
