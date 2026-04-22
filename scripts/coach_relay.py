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
COACH_ADJUST = PROJECT_ROOT / "scripts" / "coach_adjust.py"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"

POLL_INTERVAL_S = 2.0
CLI_TIMEOUT_S = 120
ADJUST_TIMEOUT_S = 60
STUCK_TURN_THRESHOLD_S = 180
SHUTDOWN = False

CONFIRM_PREFIX = "CONFIRM_ACTION"
REJECT_PREFIX = "REJECT_ACTION"
PROPOSAL_START = "[PROPOSAL]"
PROPOSAL_END = "[/PROPOSAL]"

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
        .select("id,cli_session_id,title,model")
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


STREAM_UPDATE_INTERVAL_S = 1.5
STREAM_UPDATE_MIN_CHARS = 40

MODEL_MAP = {
    "opus": "claude-opus-4-7",
    "sonnet": "claude-sonnet-4-6",
}


def call_claude_cli(
    user_message: str,
    session_id: str,
    grounding_file: Path,
    model: str = "opus",
    on_chunk: Any | None = None,
) -> str:
    model_id = MODEL_MAP.get(model, MODEL_MAP["opus"])
    cmd = [
        "claude",
        "-p", user_message,
        "--model", model_id,
        "--session-id", session_id,
        "--system-prompt-file", str(SKILL_FILE),
        "--append-system-prompt-file", str(grounding_file),
        "--output-format", "stream-json" if on_chunk else "json",
        "--max-turns", "1",
    ]

    log.info("Calling: claude -p --model %s (streaming=%s)", model_id, bool(on_chunk))

    if on_chunk:
        return _call_streaming(cmd, on_chunk)
    return _call_blocking(cmd)


def _call_blocking(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        timeout=CLI_TIMEOUT_S, cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(classify_cli_error(result.stderr.strip()[:500]))
    return _parse_json_response(result.stdout.strip())


def _call_streaming(cmd: list[str], on_chunk: Any) -> str:
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=str(PROJECT_ROOT),
    )
    accumulated = ""
    last_update = time.monotonic()
    last_update_len = 0

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            text = _extract_text_from_stream_line(line)
            if text:
                accumulated += text
                now = time.monotonic()
                new_chars = len(accumulated) - last_update_len
                if new_chars >= STREAM_UPDATE_MIN_CHARS and (now - last_update) >= STREAM_UPDATE_INTERVAL_S:
                    on_chunk(accumulated)
                    last_update = now
                    last_update_len = len(accumulated)

        proc.wait(timeout=10)
        if proc.returncode != 0:
            stderr = proc.stderr.read()[:500] if proc.stderr else ""
            raise RuntimeError(classify_cli_error(stderr))
    except Exception:
        proc.kill()
        raise

    return accumulated if accumulated else "(No response)"


def _extract_text_from_stream_line(line: str) -> str:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return ""

    if isinstance(obj, dict):
        # content_block_delta format
        delta = obj.get("delta", {})
        if isinstance(delta, dict) and delta.get("type") == "text_delta":
            return delta.get("text", "")
        # message format with result
        if "result" in obj:
            return obj["result"]
        # assistant message content blocks
        if obj.get("type") == "assistant":
            content = obj.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "".join(b.get("text", "") for b in content if b.get("type") == "text")
    return ""


def _parse_json_response(stdout: str) -> str:
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
                    return "".join(b.get("text", "") for b in content if b.get("type") == "text")
                return str(content)
        return stdout
    return json.dumps(parsed, indent=2) if isinstance(parsed, (dict, list)) else stdout


# ---------------------------------------------------------------------------
# Proposal parsing + execution
# ---------------------------------------------------------------------------

def parse_proposal(response: str) -> tuple[str, dict | None]:
    """Extract [PROPOSAL] JSON from response. Returns (clean_text, proposal_dict)."""
    start = response.find(PROPOSAL_START)
    if start == -1:
        return response, None

    end = response.find(PROPOSAL_END, start)
    if end == -1:
        return response, None

    json_str = response[start + len(PROPOSAL_START):end].strip()
    clean_text = (response[:start].rstrip() + response[end + len(PROPOSAL_END):].lstrip()).strip()

    try:
        proposal = json.loads(json_str)
    except json.JSONDecodeError:
        log.warning("Failed to parse proposal JSON: %s", json_str[:200])
        return response, None

    if not isinstance(proposal, dict) or "action" not in proposal:
        log.warning("Proposal missing 'action' key: %s", json_str[:200])
        return response, None

    return clean_text, proposal


def find_pending_proposal(sb: Any, conversation_id: str) -> dict | None:
    """Find the most recent assistant turn with a proposal in context_snapshot."""
    result = (
        sb.table("coach_turns")
        .select("id,context_snapshot")
        .eq("conversation_id", conversation_id)
        .eq("role", "assistant")
        .eq("status", "complete")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    for row in (result.data or []):
        cs = row.get("context_snapshot") or {}
        if cs.get("proposal") and not cs.get("proposal_executed"):
            return row
    return None


def execute_proposal(sb: Any, proposal: dict, proposal_turn_id: str) -> str:
    """Run coach_adjust.py for a confirmed proposal."""
    action = proposal["action"]
    target_date = proposal.get("date", date.today().isoformat())
    details = proposal.get("details", {})
    details_json = json.dumps(details)

    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [
        python, str(COACH_ADJUST),
        "--action", action,
        "--date", target_date,
        "--channel", "app_coach",
        "--details", details_json,
    ]

    log.info("Executing: %s --action %s --date %s", COACH_ADJUST.name, action, target_date)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=ADJUST_TIMEOUT_S,
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()[:300]
        log.error("coach_adjust failed (exit %d): %s", result.returncode, stderr)
        return f"The adjustment failed: {stderr}"

    try:
        output = json.loads(result.stdout)
        ok = output.get("ok", False)
        message = output.get("user_message", output.get("message", ""))
    except json.JSONDecodeError:
        ok = result.returncode == 0
        message = result.stdout.strip()[:300]

    # Mark the proposal as executed so it can't be re-confirmed
    cs = (sb.table("coach_turns")
        .select("context_snapshot")
        .eq("id", proposal_turn_id)
        .single()
        .execute()).data
    snapshot = (cs or {}).get("context_snapshot", {}) or {}
    snapshot["proposal_executed"] = True
    snapshot["proposal_result"] = {"ok": ok, "message": message}
    sb.table("coach_turns").update({"context_snapshot": snapshot}).eq("id", proposal_turn_id).execute()

    if ok:
        return f"Done — {message}" if message else "Done. Session updated."
    return f"The adjustment couldn't be applied: {message}"


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

        # Handle confirm/reject for pending proposals
        content_upper = user_content.strip().upper()
        if content_upper == CONFIRM_PREFIX or content_upper == "YES":
            proposal_turn = find_pending_proposal(sb, conversation_id)
            if proposal_turn:
                proposal = proposal_turn["context_snapshot"]["proposal"]
                log.info("Executing confirmed proposal: %s", proposal.get("action"))
                result_msg = execute_proposal(sb, proposal, proposal_turn["id"])
                write_assistant_turn(sb, conversation_id, result_msg)
                mark_turn(sb, turn_id, "complete")
                return
            else:
                write_assistant_turn(sb, conversation_id,
                    "No pending proposal to confirm. Ask me to make a change and I'll propose it first.")
                mark_turn(sb, turn_id, "complete")
                return

        if content_upper == REJECT_PREFIX or content_upper == "NO":
            proposal_turn = find_pending_proposal(sb, conversation_id)
            if proposal_turn:
                # Mark proposal as rejected
                cs = proposal_turn.get("context_snapshot", {}) or {}
                cs["proposal_executed"] = True
                cs["proposal_result"] = {"ok": False, "message": "Rejected by user"}
                sb.table("coach_turns").update({"context_snapshot": cs}).eq("id", proposal_turn["id"]).execute()
                write_assistant_turn(sb, conversation_id,
                    "Got it — keeping today's session as-is. Let me know if you'd like something else.")
                mark_turn(sb, turn_id, "complete")
                return

        conv = get_conversation(sb, conversation_id)
        if not conv:
            raise RuntimeError(f"Conversation {conversation_id} not found")

        if not conv.get("title"):
            auto_title_conversation(sb, conversation_id, user_content)

        model = conv.get("model", "opus") or "opus"
        history = get_turn_history(sb, conversation_id)
        ctx = fetch_coaching_context(sb)
        grounding = build_grounding_prompt(ctx, history)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, prefix="coach_ctx_"
        ) as f:
            f.write(grounding)
            grounding_path = Path(f.name)

        # Create a placeholder assistant turn for streaming updates
        placeholder = sb.table("coach_turns").insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": "",
            "status": "in_progress",
        }).execute()
        assistant_turn_id = placeholder.data[0]["id"] if placeholder.data else None

        def on_chunk(text_so_far: str) -> None:
            if assistant_turn_id:
                sb.table("coach_turns").update(
                    {"content": text_so_far}
                ).eq("id", assistant_turn_id).execute()

        try:
            response = call_claude_cli(
                user_message=user_content,
                session_id=conv["cli_session_id"],
                grounding_file=grounding_path,
                model=model,
                on_chunk=on_chunk,
            )
        finally:
            grounding_path.unlink(missing_ok=True)

        # Check for proposals in the response
        clean_text, proposal = parse_proposal(response)
        snapshot: dict[str, Any] = ctx.copy()
        if proposal:
            snapshot["proposal"] = proposal
            log.info("Proposal detected: action=%s", proposal.get("action"))

        if assistant_turn_id:
            sb.table("coach_turns").update({
                "content": clean_text,
                "status": "complete",
                "context_snapshot": snapshot,
            }).eq("id", assistant_turn_id).execute()
        else:
            write_assistant_turn(sb, conversation_id, clean_text, context_snapshot=snapshot)

        mark_turn(sb, turn_id, "complete")
        log.info("Turn %s answered (%d chars, model=%s, proposal=%s)",
                 turn_id[:8], len(clean_text), model, bool(proposal))

    except subprocess.TimeoutExpired:
        log.error("Turn %s timed out (%ds)", turn_id[:8], CLI_TIMEOUT_S)
        mark_turn(sb, turn_id, "error", f"Coach timed out after {CLI_TIMEOUT_S}s")
    except Exception as exc:
        log.exception("Turn %s failed", turn_id[:8])
        mark_turn(sb, turn_id, "error", str(exc)[:500])


def recover_stuck_turns(sb: Any) -> int:
    """Re-mark turns stuck in 'in_progress' for longer than the threshold as 'error'.
    This handles daemon crashes mid-processing — without it the user's turn
    shows "Coach is thinking…" forever."""
    cutoff = datetime.now(timezone.utc).isoformat()
    result = (
        sb.table("coach_turns")
        .select("id,created_at")
        .eq("status", "in_progress")
        .execute()
    )
    recovered = 0
    for row in (result.data or []):
        created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        age_s = (datetime.now(timezone.utc) - created).total_seconds()
        if age_s > STUCK_TURN_THRESHOLD_S:
            mark_turn(sb, row["id"], "error",
                      f"Turn was stuck in_progress for {int(age_s)}s — daemon likely crashed. Please retry.")
            recovered += 1
    if recovered:
        log.warning("Recovered %d stuck turn(s) from prior crash", recovered)
    return recovered


def check_claude_auth() -> tuple[bool, str]:
    """Check if Claude CLI is authenticated via Max subscription."""
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            return True, output
        return False, output
    except FileNotFoundError:
        return False, "claude CLI not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "claude auth status timed out"


def classify_cli_error(stderr: str) -> str:
    """Turn cryptic CLI errors into user-friendly messages."""
    lower = stderr.lower()
    if "rate" in lower and "limit" in lower or "429" in lower or "too many" in lower:
        return "Opus quota exhausted — try again in a few minutes, or ask a simpler question (uses less quota)."
    if "auth" in lower or "unauthorized" in lower or "401" in lower:
        return "Coach authentication expired. Run `claude login` on the Mac to re-authenticate."
    if "timeout" in lower or "timed out" in lower:
        return f"Coach timed out after {CLI_TIMEOUT_S}s. Try a shorter question."
    return f"Coach error: {stderr[:200]}"


def run_loop(live: bool) -> None:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    if live and not check_claude_cli():
        log.error("claude CLI not found in PATH — falling back to echo mode")
        live = False

    if live:
        auth_ok, auth_msg = check_claude_auth()
        if not auth_ok:
            log.error("Claude auth check failed: %s", auth_msg)
            log.error("Run `claude login` to authenticate, then restart the relay.")
            sys.exit(1)
        log.info("Claude auth OK")

    recover_stuck_turns(sb)
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
