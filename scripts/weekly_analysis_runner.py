#!/usr/bin/env python3
"""Weekly analysis orchestrator for Ascent.

Runs interference analysis and decision retrospective in sequence.
Designed to be called by launchd every Sunday at 20:00.

Usage:
    python weekly_analysis_runner.py              # run both analyses
    python weekly_analysis_runner.py --dry-run    # print without writing to DB
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weekly_analysis")

ANALYSES = [
    {
        "name": "Interference Analysis",
        "script": "interference_analysis.py",
        "args": ["--lookback", "90"],
    },
    {
        "name": "Decision Retrospective",
        "script": "decision_retrospective.py",
        "args": ["--lookback", "14"],
    },
]


def run_analysis(name: str, script: str, extra_args: list, dry_run: bool) -> bool:
    """Run a single analysis script. Returns True on success."""
    cmd = [PYTHON, str(SCRIPTS_DIR / script)] + extra_args
    if dry_run:
        cmd.append("--dry-run")

    log.info("Starting: %s", name)
    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(SCRIPTS_DIR.parent),
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            log.info("%s completed in %.1fs", name, elapsed)
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n")[-5:]:
                    log.info("  %s", line)
            return True
        else:
            log.error("%s failed (exit %d) in %.1fs", name, result.returncode, elapsed)
            if result.stderr.strip():
                for line in result.stderr.strip().split("\n")[-5:]:
                    log.error("  %s", line)
            return False

    except subprocess.TimeoutExpired:
        log.error("%s timed out after 300s", name)
        return False
    except Exception as e:
        log.error("%s error: %s", name, e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run weekly Ascent analyses")
    parser.add_argument("--dry-run", action="store_true", help="Pass --dry-run to each script")
    args = parser.parse_args()

    log.info("=== Weekly Analysis Run ===")
    start = time.time()

    results = {}
    for analysis in ANALYSES:
        success = run_analysis(
            analysis["name"],
            analysis["script"],
            analysis["args"],
            dry_run=args.dry_run,
        )
        results[analysis["name"]] = success

    elapsed = time.time() - start
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    log.info("=== Done: %d/%d succeeded in %.1fs ===", passed, total, elapsed)
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        log.info("  %s: %s", name, status)

    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
