#!/usr/bin/env python3
"""Deploy Ascent schema and seed data to Supabase via direct PostgreSQL connection.

Usage:
    pip install psycopg2-binary python-dotenv
    python scripts/deploy_schema.py
"""

import os
import sys
import glob
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("ERROR: SUPABASE_DB_URL not set in .env")
    sys.exit(1)

SQL_DIR = PROJECT_DIR / "sql"
sql_files = sorted(SQL_DIR.glob("0*.sql"))

if not sql_files:
    print(f"ERROR: No SQL files found in {SQL_DIR}")
    sys.exit(1)

print("=== Deploying Ascent schema to Supabase ===\n")

conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cur = conn.cursor()

for sql_file in sql_files:
    print(f"Running {sql_file.name}...")
    sql = sql_file.read_text()
    try:
        cur.execute(sql)
        print(f"  Done.")
    except Exception as e:
        print(f"  ERROR: {e}")
        conn.rollback()
        conn.autocommit = True

print("\n=== Verifying deployment ===\n")

cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = cur.fetchall()
print("Tables created:")
for t in tables:
    print(f"  - {t[0]}")

print()

for check in [
    ("biomarker_definitions", "biomarkers"),
    ("exercises", "exercises"),
    ("blood_test_results", "blood test results"),
]:
    cur.execute(f"SELECT count(*) FROM {check[0]};")
    count = cur.fetchone()[0]
    print(f"  {check[1]}: {count} rows")

cur.close()
conn.close()

print("\n=== Deployment complete ===")
