#!/bin/bash
# Deploy Ascent schema and seed data to Supabase
# Usage: ./scripts/deploy_schema.sh
# Requires: psql, .env file with SUPABASE_DB_URL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load .env
if [ -f "$PROJECT_DIR/.env" ]; then
  export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
else
  echo "ERROR: .env file not found at $PROJECT_DIR/.env"
  exit 1
fi

if [ -z "${SUPABASE_DB_URL:-}" ]; then
  echo "ERROR: SUPABASE_DB_URL not set in .env"
  exit 1
fi

SQL_DIR="$PROJECT_DIR/sql"

echo "=== Deploying Ascent schema to Supabase ==="

for sql_file in "$SQL_DIR"/0*.sql; do
  echo "Running $(basename "$sql_file")..."
  psql "$SUPABASE_DB_URL" -f "$sql_file"
  echo "  Done."
done

echo ""
echo "=== Verifying deployment ==="
psql "$SUPABASE_DB_URL" -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
"

echo ""
echo "=== Checking seed data ==="
psql "$SUPABASE_DB_URL" -c "SELECT count(*) AS biomarker_count FROM biomarker_definitions;"
psql "$SUPABASE_DB_URL" -c "SELECT count(*) AS exercise_count FROM exercises;"
psql "$SUPABASE_DB_URL" -c "SELECT count(*) AS blood_test_result_count FROM blood_test_results;"

echo ""
echo "=== Deployment complete ==="
