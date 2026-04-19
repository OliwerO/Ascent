#!/usr/bin/env python3
"""Mac-side daemon that answers in-app coach questions via Claude Code CLI.

Watches coach_turns for pending user messages, builds a grounded system
prompt, pipes it to `claude -p` (routed through the Max subscription),
and writes the response back to Supabase. The React app picks up changes
via Supabase realtime.

Phase A: echo mode. Skips the CLI entirely and just writes back a
"pong: {content}" response. Proves the Supabase round-trip before we
burn any Opus quota.

Phase B (later): wire to `claude -p --model claude-opus-4-7` using the
conversation's cli_session_id for multi-turn continuity.

Usage:
    venv/bin/python scripts/coach_relay.py           # echo mode
    venv/bin/python scripts/coach_relay.py --live    # enables CLI (Phase B+)
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

POLL_INTERVAL_S = 2.0
SHUTDOWN = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("coach_relay")


def handle_signal(signum: int, _frame: Any) -> None:
    global SHUTDOWN
    log.info("Received signal %s — shutting down after current turn", signum)
    SHUTDOWN = True


def fetch_pending_turn(sb) -> dict | None:
    """Pick the oldest pending user turn, if any."""
    result = (
        sb.table("coach_turns")
        .select("id,conversation_id,content,created_at")
        .eq("status", "pending")
        .eq("role", "user")
        .order("created_at")
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def mark_turn_in_progress(sb, turn_id: str) -> None:
    sb.table("coach_turns").update({"status": "in_progress"}).eq("id", turn_id).execute()


def mark_turn_complete(sb, turn_id: str) -> None:
    sb.table("coach_turns").update({"status": "complete"}).eq("id", turn_id).execute()


def mark_turn_error(sb, turn_id: str, message: str) -> None:
    sb.table("coach_turns").update(
        {"status": "error", "error": message}
    ).eq("id", turn_id).execute()


def write_assistant_turn(
    sb,
    conversation_id: str,
    content: str,
    context_snapshot: dict | None = None,
    kb_refs: list[str] | None = None,
) -> None:
    sb.table("coach_turns").insert(
        {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": content,
            "status": "complete",
            "context_snapshot": context_snapshot,
            "kb_refs": kb_refs,
        }
    ).execute()


def generate_echo_response(user_content: str) -> str:
    """Phase A stand-in. Replace with Claude CLI call in Phase B."""
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    return (
        f"echo ({stamp}): {user_content}\n\n"
        "Relay is online. Real coach responses land once Phase B wires the Claude CLI."
    )


def process_turn(sb, turn: dict, live: bool) -> None:
    turn_id = turn["id"]
    conversation_id = turn["conversation_id"]
    user_content = turn["content"]

    log.info("Processing turn %s (%s chars)", turn_id[:8], len(user_content))
    mark_turn_in_progress(sb, turn_id)

    try:
        if live:
            # Phase B: call Claude CLI here.
            raise NotImplementedError("--live mode wires up in Phase B")
        response = generate_echo_response(user_content)
        write_assistant_turn(sb, conversation_id, response)
        mark_turn_complete(sb, turn_id)
        log.info("Turn %s answered (echo)", turn_id[:8])
    except Exception as exc:  # noqa: BLE001 — surface any failure to the UI
        log.exception("Turn %s failed", turn_id[:8])
        mark_turn_error(sb, turn_id, str(exc))


def run_loop(live: bool) -> None:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    log.info("Coach relay started (live=%s, poll=%.1fs)", live, POLL_INTERVAL_S)

    while not SHUTDOWN:
        try:
            turn = fetch_pending_turn(sb)
            if turn:
                process_turn(sb, turn, live)
                continue
        except Exception:  # noqa: BLE001
            log.exception("Poll loop error — continuing")
        time.sleep(POLL_INTERVAL_S)

    log.info("Coach relay stopped")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ascent coach relay daemon")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use Claude CLI (Phase B+). Default is echo mode.",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    run_loop(live=args.live)
    return 0


if __name__ == "__main__":
    sys.exit(main())
