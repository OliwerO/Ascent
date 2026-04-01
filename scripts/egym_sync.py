#!/usr/bin/env python3
"""eGym body scan → Supabase sync script.

Authenticates against the eGym/Netpulse API, fetches body composition
and bio age data, and upserts into the body_composition table with
source='egym'.

Usage:
    python egym_sync.py                    # sync latest scan
    python egym_sync.py --date 2026-04-01  # override date

Requires: EGYM_BRAND, EGYM_USERNAME, EGYM_PASSWORD in .env
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from supabase import create_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

EGYM_BRAND = os.environ["EGYM_BRAND"]
EGYM_USERNAME = os.environ["EGYM_USERNAME"]
EGYM_PASSWORD = os.environ["EGYM_PASSWORD"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

NETPULSE_URL = f"https://{EGYM_BRAND}.netpulse.com"
EGYM_API_URL = "https://mobile-api.int.api.egym.com"
API_DELAY = 0.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("egym_sync")


# ---------------------------------------------------------------------------
# eGym API client
# ---------------------------------------------------------------------------


class EgymClient:
    """eGym/Netpulse API client.

    Auth flow: POST login to {brand}.netpulse.com → get JSESSIONID cookie →
    forward cookie manually to mobile-api.int.api.egym.com for data endpoints.
    """

    def __init__(self, brand: str, username: str, password: str):
        self.netpulse_url = f"https://{brand}.netpulse.com"
        self.api_url = EGYM_API_URL
        self.username = username
        self.password = password
        self.cookie = ""
        self.user_id = None

    def login(self) -> dict:
        """Authenticate via Netpulse and return user profile."""
        resp = requests.post(
            f"{self.netpulse_url}/np/exerciser/login",
            data=urlencode({
                "username": self.username,
                "password": self.password,
                "relogin": "false",
            }),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"eGym login failed (HTTP {resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self.user_id = data["uuid"]
        self.cookie = resp.headers.get("Set-Cookie", "")
        log.info("Logged in as %s %s (club: %s)",
                 data.get("firstName"), data.get("lastName"),
                 data.get("homeClubName"))
        return data

    def _get(self, url: str) -> requests.Response:
        """GET with auth cookie forwarding and rate limiting."""
        time.sleep(API_DELAY)
        return requests.get(
            url,
            headers={"Accept": "application/json", "Cookie": self.cookie},
        )

    def get_body_metrics(self) -> list[dict]:
        """Fetch latest body composition metrics from Seca scanner."""
        resp = self._get(
            f"{self.api_url}/measurements/api/v1.0/exercisers/{self.user_id}/body/latest"
        )
        if resp.status_code != 200:
            log.warning("Body metrics failed (HTTP %d): %s",
                        resp.status_code, resp.text[:200])
            return []
        data = resp.json()
        return data if isinstance(data, list) else [data]

    def get_bio_age(self) -> dict | None:
        """Fetch biological age breakdown."""
        resp = self._get(
            f"{self.api_url}/analysis/api/v1.0/exercisers/{self.user_id}/bioage"
        )
        if resp.status_code != 200:
            log.warning("Bio age failed (HTTP %d)", resp.status_code)
            return None
        return resp.json()

    def get_strength(self) -> list[dict]:
        """Fetch strength assessment data."""
        resp = self._get(
            f"{self.api_url}/measurements/api/v1.0/exercisers/{self.user_id}/strength/latest"
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data if isinstance(data, list) else [data]

    def get_flexibility(self) -> list[dict]:
        """Fetch flexibility assessment data."""
        resp = self._get(
            f"{self.api_url}/measurements/api/v1.0/exercisers/{self.user_id}/flexibility/latest"
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data if isinstance(data, list) else [data]


# ---------------------------------------------------------------------------
# Metric extraction → body_composition columns
# ---------------------------------------------------------------------------

# Maps eGym metric type strings to (column_name, converter_fn).
# Only primary metrics — LOW/TOP/MID/MIN/MAX ranges go to raw_json.
METRIC_MAP = {
    "WEIGHT_KG":                    ("weight_grams", lambda v: int(v * 1000)),
    "BMI":                          ("bmi", float),
    "BODY_FAT_PERCENTS":            ("body_fat_pct", float),
    "BODY_WATER_PERCENTS":          ("body_water_pct", float),
    "BODY_WATER_LITER":             (None, None),  # raw_json only
    "SKELETAL_MUSCLE_MASS_KG":      ("muscle_mass_grams", lambda v: int(v * 1000)),
    "BODY_FAT_MASS_KG":             (None, None),  # raw_json only (lean mass computed)
}


def extract_body_comp(metrics: list[dict]) -> tuple[dict, list[dict]]:
    """Convert eGym body metric entries into body_composition row fields."""
    row = {}
    raw_entries = []

    for entry in metrics:
        metric_type = entry.get("type", "")
        value = entry.get("value")
        if value is None:
            continue

        value = float(value)
        raw_entries.append({
            "type": metric_type,
            "value": value,
            "source": entry.get("source", ""),
            "source_label": entry.get("sourceLabel", ""),
            "created_at": entry.get("createdAt", ""),
        })

        if metric_type in METRIC_MAP:
            col, converter = METRIC_MAP[metric_type]
            if col and col not in row:
                row[col] = converter(value)

    # Compute lean body mass if we have weight and fat mass
    weight_g = row.get("weight_grams")
    fat_mass_entries = [e for e in raw_entries if e["type"] == "BODY_FAT_MASS_KG"]
    if weight_g and fat_mass_entries:
        fat_mass_g = int(fat_mass_entries[0]["value"] * 1000)
        row["lean_body_mass_grams"] = weight_g - fat_mass_g

    return row, raw_entries


def extract_bio_age_summary(bio_age: dict) -> dict:
    """Flatten bio age response into a simple dict for raw_json."""
    if not bio_age:
        return {}
    result = {}
    for section_key, section in bio_age.items():
        if not isinstance(section, dict):
            continue
        for key, val in section.items():
            if isinstance(val, dict) and "value" in val:
                result[key] = val["value"]
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Sync eGym body scans to Supabase")
    parser.add_argument(
        "--date", type=str, default=date.today().isoformat(),
        help="Date to assign to the scan (YYYY-MM-DD, default: today)",
    )
    args = parser.parse_args()
    scan_date = args.date

    # Authenticate
    client = EgymClient(EGYM_BRAND, EGYM_USERNAME, EGYM_PASSWORD)
    client.login()

    # Fetch body metrics
    raw_body = client.get_body_metrics()
    log.info("Got %d body metric entries", len(raw_body))

    # Fetch supplementary data
    bio_age = client.get_bio_age()
    strength = client.get_strength()
    flexibility = client.get_flexibility()

    # Extract body composition fields
    body_row, raw_entries = extract_body_comp(raw_body)
    bio_summary = extract_bio_age_summary(bio_age)

    if not body_row:
        log.warning("No body composition data found")
        if raw_body:
            log.info("Raw types: %s", [e.get("type") for e in raw_body[:10]])
        sys.exit(1)

    # Build upsert row
    row = {
        "date": scan_date,
        "source": "egym",
        **body_row,
        "raw_json": json.loads(json.dumps({
            "body_metrics": raw_entries,
            "bio_age": bio_summary,
            "strength_count": len(strength),
            "flexibility_count": len(flexibility),
            "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, default=str)),
    }

    # Log what we're inserting
    for col, val in sorted(body_row.items()):
        log.info("  %s = %s", col, val)
    if bio_summary:
        log.info("  bio_age: %s", bio_summary)

    # Upsert to Supabase
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    sb.table("body_composition").upsert(
        row, on_conflict="date,source"
    ).execute()
    log.info("body_composition upserted for %s (source=egym)", scan_date)


if __name__ == "__main__":
    main()
