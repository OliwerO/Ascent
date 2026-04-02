#!/usr/bin/env python3
"""Xiaomi Mi Scale (via Zepp Life / SmartScaleConnect) → Supabase sync.

Runs the scaleconnect binary to pull weight data from Zepp Life cloud,
parses the CSV export, and upserts into the body_composition table.

Usage:
    python scale_sync.py                # sync all new data
    python scale_sync.py --dry-run      # log what would be written, don't write
"""

import argparse
import csv
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

SCALECONNECT_BIN = PROJECT_ROOT / "bin" / "scaleconnect"
EXPORT_CSV = PROJECT_ROOT / "data" / "scale_export.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scale_sync")


# ---------------------------------------------------------------------------
# SmartScaleConnect runner
# ---------------------------------------------------------------------------


def run_scaleconnect() -> bool:
    """Run scaleconnect binary to export fresh data from Zepp Life."""
    email = os.environ.get("XIAOMI_EMAIL")
    password = os.environ.get("XIAOMI_PASSWORD")
    if not email or not password:
        log.error("XIAOMI_EMAIL and XIAOMI_PASSWORD must be set in .env")
        return False

    # Build inline config with proper JSON escaping
    config = json.dumps({
        "sync_weight": {
            "from": f"zepp/xiaomi {email} {password}",
            "to": f"csv {EXPORT_CSV}",
        }
    })

    log.info("Running scaleconnect to pull from Zepp Life...")
    try:
        result = subprocess.run(
            [str(SCALECONNECT_BIN), "-c", config],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            log.error("scaleconnect failed (exit %d): %s", result.returncode, result.stderr.strip())
            return False
        if result.stdout.strip():
            log.info("scaleconnect: %s", result.stdout.strip())
        return True
    except FileNotFoundError:
        log.error("scaleconnect binary not found at %s", SCALECONNECT_BIN)
        return False
    except subprocess.TimeoutExpired:
        log.error("scaleconnect timed out after 120s")
        return False


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------


def _safe_float(val: str | None) -> float | None:
    """Parse a string to float, returning None on empty/invalid."""
    if not val or not val.strip():
        return None
    try:
        v = float(val.strip())
        return v if v > 0 else None
    except ValueError:
        return None


def _safe_int(val: str | None) -> int | None:
    """Parse a string to int, returning None on empty/invalid."""
    f = _safe_float(val)
    return int(round(f)) if f is not None else None


def parse_export(csv_path: Path) -> list[dict]:
    """Parse scaleconnect CSV export into row dicts for Supabase.

    CSV columns: Date,Weight,BMI,BodyFat,BodyWater,BoneMass,MetabolicAge,
                 MuscleMass,PhysiqueRating,ProteinMass,VisceralFat,
                 BasalMetabolism,HeartRate,SkeletalMuscleMass,User,Source

    Deduplicates by date — keeps the earliest reading per day (fasted weight).
    """
    if not csv_path.exists():
        log.error("Export CSV not found: %s", csv_path)
        return []

    seen_dates: dict[str, dict] = {}  # date_str → row (first wins)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for line in reader:
            date_str = line.get("Date", "").strip()
            weight_str = line.get("Weight", "").strip()

            if not date_str or not weight_str:
                continue

            try:
                weight_kg = float(weight_str)
            except ValueError:
                log.warning("Skipping row with invalid weight: %s", weight_str)
                continue

            if weight_kg <= 0:
                continue

            # Parse date — format is "2006-01-02 15:04:05"
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                except ValueError:
                    log.warning("Skipping row with unparseable date: %s", date_str)
                    continue

            day_key = dt.strftime("%Y-%m-%d")

            # Keep first reading per day (earliest = fasted weight)
            if day_key in seen_dates:
                log.debug("Duplicate date %s — keeping earliest reading", day_key)
                continue

            weight_grams = int(round(weight_kg * 1000))

            # Convert bone/muscle mass from kg to grams (scaleconnect outputs kg)
            bone_mass_kg = _safe_float(line.get("BoneMass"))
            muscle_mass_kg = _safe_float(line.get("MuscleMass"))

            row = {
                "date": day_key,
                "weight_grams": weight_grams,
                "bmi": _safe_float(line.get("BMI")),
                "body_fat_pct": _safe_float(line.get("BodyFat")),
                "body_water_pct": _safe_float(line.get("BodyWater")),
                "bone_mass_grams": int(round(bone_mass_kg * 1000)) if bone_mass_kg else None,
                "muscle_mass_grams": int(round(muscle_mass_kg * 1000)) if muscle_mass_kg else None,
                "visceral_fat_rating": _safe_float(line.get("VisceralFat")),
                "metabolic_age": _safe_int(line.get("MetabolicAge")),
                "source": "xiaomi",
                "raw_json": {k: v for k, v in line.items() if v},
            }
            seen_dates[day_key] = row

    rows = list(seen_dates.values())
    log.info("Parsed %d weight entries from CSV (%d unique dates)",
             sum(1 for _ in open(csv_path)) - 1 if csv_path.exists() else 0, len(rows))
    return rows


# ---------------------------------------------------------------------------
# Supabase upsert
# ---------------------------------------------------------------------------


def upsert_weights(sb, rows: list[dict], dry_run: bool = False) -> int:
    """Upsert weight rows into body_composition. Returns count written."""
    if not rows:
        return 0

    # Fetch existing xiaomi rows to skip duplicates
    existing = (
        sb.table("body_composition")
        .select("date")
        .eq("source", "xiaomi")
        .execute()
    )
    existing_dates = {r["date"] for r in existing.data} if existing.data else set()

    written = 0
    for row in rows:
        if row["date"] in existing_dates:
            log.debug("Skipping %s — already in Supabase", row["date"])
            continue

        if dry_run:
            log.info("[DRY RUN] Would upsert: date=%s weight_grams=%d (%.1f kg)",
                     row["date"], row["weight_grams"], row["weight_grams"] / 1000)
            written += 1
            continue

        try:
            sb.table("body_composition").upsert(
                row, on_conflict="date,source"
            ).execute()
            written += 1
            log.info("Upserted: date=%s weight_grams=%d (%.1f kg)",
                     row["date"], row["weight_grams"], row["weight_grams"] / 1000)
        except Exception as exc:
            log.error("Failed to upsert %s: %s", row["date"], exc)

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Sync Xiaomi scale weight to Supabase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log what would be written without writing")
    parser.add_argument("--skip-export", action="store_true",
                        help="Skip running scaleconnect, use existing CSV")
    args = parser.parse_args()

    # Step 1: Export fresh data from Zepp Life
    if not args.skip_export:
        if not run_scaleconnect():
            log.error("Failed to export data from Zepp Life")
            sys.exit(1)
    else:
        if not EXPORT_CSV.exists():
            log.error("--skip-export used but CSV not found: %s", EXPORT_CSV)
            sys.exit(1)

    # Step 2: Parse the CSV
    rows = parse_export(EXPORT_CSV)
    if not rows:
        log.warning("No weight data found in export")
        sys.exit(1)

    # Step 3: Upsert to Supabase
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    written = upsert_weights(sb, rows, dry_run=args.dry_run)

    prefix = "[DRY RUN] " if args.dry_run else ""
    log.info("%sSync complete: %d new entries written, %d total in CSV",
             prefix, written, len(rows))


if __name__ == "__main__":
    main()
