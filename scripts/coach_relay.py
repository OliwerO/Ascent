#!/usr/bin/env python3
"""Mac-side daemon that answers in-app coach questions via Claude Code CLI.

Watches coach_turns for pending user messages, builds a grounded system
prompt with today's coaching context, pipes it to `claude -p` (routed
through the Max subscription), and writes the response back to Supabase.
The React app picks up changes via Supabase realtime.

Usage:
    venv/bin/python scripts/coach_relay.py           # echo mode (no CLI)
    venv/bin/python scripts/coach_relay.py --live     # Claude CLI via Max
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

SKILL_FILE = PROJECT_ROOT / "openclaw" / "skills" / "coach-chat" / "SKILL.md"

POLL_INTERVAL_S = 2.0
CLI_TIMEOUT_S = 120
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


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def fetch_pending_turn(sb: Any) -> dict | None:
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


def get_conversation(sb: Any, conv_id: str) -> dict | None:
    result = (
        sb.table("coach_conversations")
        .select("id,cli_session_id,title")
        .eq("id", conv_id)
        .single()
        .execute()
    )
    return result.data


def get_turn_history(sb: Any, conv_id: str, limit: int = 20) -> list[dict]:
    result = (
        sb.table("coach_turns")
        .select("role,content,created_at")
        .eq("conversation_id", conv_id)
        .eq("status", "complete")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = result.data or []
    rows.reverse()
    return rows


def mark_turn(sb: Any, turn_id: str, status: str, error: str | None = None) -> None:
    update: dict[str, Any] = {"status": status}
    if error:
        update["error"] = error
    sb.table("coach_turns").update(update).eq("id", turn_id).execute()


def write_assistant_turn(
    sb: Any,
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


def auto_title_conversation(sb: Any, conv_id: str, first_message: str) -> None:
    title = first_message[:60].strip()
    if len(first_message) > 60:
        title = title.rsplit(" ", 1)[0] + "…"
    sb.table("coach_conversations").update({"title": title}).eq("id", conv_id).execute()


# ---------------------------------------------------------------------------
# Grounding context
# ---------------------------------------------------------------------------

def fetch_coaching_context(sb: Any) -> dict:
    today_str = date.today().isoformat()
    ctx: dict[str, Any] = {"date": today_str}

    try:
        r = sb.table("daily_coaching_context").select("*").limit(1).execute()
        if r.data:
            ctx["daily_coaching_context"] = r.data[0]
    except Exception:
        log.debug("daily_coaching_context not available")

    try:
        r = (
            sb.table("coaching_log")
            .select("date,type,message,decision_type,rule,kb_refs,inputs")
            .order("date", desc=True)
            .limit(7)
            .execute()
        )
        ctx["recent_decisions"] = r.data or []
    except Exception:
        log.debug("coaching_log not available")

    try:
        r = (
            sb.table("planned_workouts")
            .select("session_name,session_type,scheduled_date,status,adjustment_reason,workout_definition")
            .eq("scheduled_date", today_str)
            .limit(1)
            .execute()
        )
        if r.data:
            ctx["todays_workout"] = r.data[0]
    except Exception:
        log.debug("planned_workouts not available")

    try:
        r = (
            sb.table("subjective_wellness")
            .select("date,composite_score,energy,muscle_soreness,motivation,stress,sleep_quality")
            .eq("date", today_str)
            .limit(1)
            .execute()
        )
        if r.data:
            ctx["todays_wellness"] = r.data[0]
    except Exception:
        log.debug("subjective_wellness not available")

    return ctx


def build_grounding_prompt(ctx: dict, history: list[dict]) -> str:
    lines = [
        f"## Today: {ctx.get('date', 'unknown')}",
        "",
    ]

    dcc = ctx.get("daily_coaching_context")
    if dcc:
        lines.append("### Recovery signals")
        for key in ("hrv_status", "sleep_hours", "body_battery_highest",
                     "training_readiness_score", "hard_override"):
            if key in dcc and dcc[key] is not None:
                lines.append(f"- {key}: {dcc[key]}")
        lines.append("")

    tw = ctx.get("todays_workout")
    if tw:
        lines.append("### Today's session")
        lines.append(f"- Session: {tw.get('session_name')} ({tw.get('session_type')})")
        lines.append(f"- Status: {tw.get('status')}")
        if tw.get("adjustment_reason"):
            lines.append(f"- Adjustment: {tw['adjustment_reason']}")
        lines.append("")

    wellness = ctx.get("todays_wellness")
    if wellness:
        lines.append("### Today's wellness")
        for key in ("composite_score", "energy", "muscle_soreness", "motivation", "stress", "sleep_quality"):
            if key in wellness and wellness[key] is not None:
                lines.append(f"- {key}: {wellness[key]}")
        lines.append("")

    decisions = ctx.get("recent_decisions", [])
    if decisions:
        lines.append("### Recent coaching decisions (last 7)")
        for d in decisions[:7]:
            rule = d.get("rule") or "no rule"
            lines.append(f"- {d.get('date')}: {d.get('decision_type', d.get('type', '?'))} — {d.get('message', '')[:80]} (rule: {rule})")
        lines.append("")

    if history:
        lines.append("### Conversation so far")
        for turn in history[-10:]:
            role = turn["role"].upper()
            lines.append(f"[{role}] {turn['content'][:500]}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude CLI integration
# ---------------------------------------------------------------------------

def check_claude_cli() -> bool:
    return shutil.which("claude") is not None


def call_claude_cli(
    user_message: str,
    session_id: str,
    grounding_file: Path,
) -> str:
    cmd = [
        "claude",
        "-p", user_message,
        "--model", "claude-opus-4-7",
        "--session-id", session_id,
        "--system-prompt-file", str(SKILL_FILE),
        "--append-system-prompt-file", str(grounding_file),
        "--output-format", "json",
        "--max-turns", "1",
    ]

    log.info("Calling: %s", " ".join(cmd[:6]) + " ...")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=CLI_TIMEOUT_S,
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()[:500]
        log.error("claude -p failed (exit %d): %s", result.returncode, stderr)
        raise RuntimeError(f"Claude CLI exited {result.returncode}: {stderr}")

    stdout = result.stdout.strip()
    if not stdout:
        raise RuntimeError("Claude CLI returned empty output")

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout

    if isinstance(parsed, dict) and "result" in parsed:
        return parsed["result"]
    if isinstance(parsed, list):
        for msg in reversed(parsed):
            if isinstance(msg, dict) and msg.get("type") == "assistant":
                content = msg.get("content", "")
                if isinstance(content, list):
                    texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                    return "\n".join(texts)
                return str(content)
        return stdout

    return json.dumps(parsed, indent=2) if isinstance(parsed, (dict, list)) else stdout


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def generate_echo_response(user_content: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    return (
        f"echo ({stamp}): {user_content}\n\n"
        "Relay is online. Start with `--live` to enable Opus."
    )


def process_turn(sb: Any, turn: dict, live: bool) -> None:
    turn_id = turn["id"]
    conversation_id = turn["conversation_id"]
    user_content = turn["content"]

    log.info("Processing turn %s (%d chars)", turn_id[:8], len(user_content))
    mark_turn(sb, turn_id, "in_progress")

    try:
        if not live:
            response = generate_echo_response(user_content)
            write_assistant_turn(sb, conversation_id, response)
            mark_turn(sb, turn_id, "complete")
            return

        conv = get_conversation(sb, conversation_id)
        if not conv:
            raise RuntimeError(f"Conversation {conversation_id} not found")

        if not conv.get("title"):
            auto_title_conversation(sb, conversation_id, user_content)

        history = get_turn_history(sb, conversation_id)
        ctx = fetch_coaching_context(sb)
        grounding = build_grounding_prompt(ctx, history)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, prefix="coach_ctx_"
        ) as f:
            f.write(grounding)
            grounding_path = Path(f.name)

        try:
            response = call_claude_cli(
                user_message=user_content,
                session_id=conv["cli_session_id"],
                grounding_file=grounding_path,
            )
        finally:
            grounding_path.unlink(missing_ok=True)

        write_assistant_turn(
            sb,
            conversation_id,
            response,
            context_snapshot=ctx,
        )
        mark_turn(sb, turn_id, "complete")
        log.info("Turn %s answered (%d chars)", turn_id[:8], len(response))

    except subprocess.TimeoutExpired:
        log.error("Turn %s timed out (%ds)", turn_id[:8], CLI_TIMEOUT_S)
        mark_turn(sb, turn_id, "error", f"Coach timed out after {CLI_TIMEOUT_S}s")
    except Exception as exc:
        log.exception("Turn %s failed", turn_id[:8])
        mark_turn(sb, turn_id, "error", str(exc)[:500])


def run_loop(live: bool) -> None:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    if live and not check_claude_cli():
        log.error("claude CLI not found in PATH — falling back to echo mode")
        live = False

    log.info("Coach relay started (live=%s, poll=%.1fs)", live, POLL_INTERVAL_S)

    while not SHUTDOWN:
        try:
            turn = fetch_pending_turn(sb)
            if turn:
                process_turn(sb, turn, live)
                continue
        except Exception:
            log.exception("Poll loop error — continuing")
        time.sleep(POLL_INTERVAL_S)

    log.info("Coach relay stopped")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ascent coach relay daemon")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use Claude CLI (Opus via Max). Default is echo mode.",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    run_loop(live=args.live)
    return 0


if __name__ == "__main__":
    sys.exit(main())
