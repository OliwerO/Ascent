#!/usr/bin/env python3
"""Verify that recent SQL migrations have been applied to Supabase.

Checks for:
  - sql/030_wellness_late_override.sql  (trigger fn_wellness_late_override)
  - sql/031_status_state_machine.sql    (trigger fn_planned_workouts_status_guard)
  - sql/032_coach_conversations.sql     (tables coach_conversations, coach_turns)

Usage:
    venv/bin/python scripts/verify_migrations.py
    venv/bin/python scripts/verify_migrations.py --apply   # apply missing ones
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("ERROR: SUPABASE_DB_URL not set in .env")
    sys.exit(1)

CHECKS = [
    {
        "migration": "030_wellness_late_override.sql",
        "description": "Wellness late-override trigger",
        "check_sql": """
            SELECT 1 FROM pg_trigger
            WHERE tgname = 'trg_wellness_late_override'
        """,
    },
    {
        "migration": "031_status_state_machine.sql",
        "description": "Planned workouts status state machine",
        "check_sql": """
            SELECT 1 FROM pg_trigger
            WHERE tgname = 'trg_planned_workouts_status_guard'
        """,
    },
    {
        "migration": "032_coach_conversations.sql",
        "description": "Coach conversations + turns tables",
        "check_sql": """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'coach_conversations'
        """,
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply missing migrations")
    args = parser.parse_args()

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    missing = []
    print("=== Migration verification ===\n")

    for check in CHECKS:
        cur.execute(check["check_sql"])
        found = cur.fetchone() is not None
        status = "APPLIED" if found else "MISSING"
        icon = "✓" if found else "✗"
        print(f"  {icon} {check['migration']:40s} {status:8s}  ({check['description']})")
        if not found:
            missing.append(check["migration"])

    if not missing:
        print("\nAll migrations applied.")
        cur.close()
        conn.close()
        return 0

    print(f"\n{len(missing)} migration(s) missing.")

    if not args.apply:
        print("Run with --apply to apply them.\n")
        cur.close()
        conn.close()
        return 1

    sql_dir = PROJECT_ROOT / "sql"
    for name in missing:
        sql_file = sql_dir / name
        if not sql_file.exists():
            print(f"  ERROR: {sql_file} not found")
            continue
        print(f"\n  Applying {name}...")
        sql = sql_file.read_text()
        try:
            cur.execute(sql)
            print(f"  Done.")
        except Exception as e:
            print(f"  ERROR: {e}")
            conn.rollback()
            conn.autocommit = True

    print("\n=== Re-verifying ===\n")
    for check in CHECKS:
        cur.execute(check["check_sql"])
        found = cur.fetchone() is not None
        icon = "✓" if found else "✗"
        print(f"  {icon} {check['migration']:40s} {'APPLIED' if found else 'STILL MISSING'}")

    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
