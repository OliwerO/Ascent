# Block Review

**Schedule:** On-demand (manual trigger) + one-time scheduled for Block 1 (Apr 27) and Block 2 (May 25)
**Model:** Opus 1M
**Purpose:** End-of-block training review, interactive planning session

---

You are running a training block review for the Ascent coaching system. Use Opus-level analytical depth.

STEP 1 — DETERMINE CURRENT BLOCK:
  source /Users/jarvisforoli/projects/ascent/.env
  curl -s "${SUPABASE_URL}/rest/v1/daily_coaching_context?select=block_number,block_name,current_week&limit=1" -H "apikey: ${SUPABASE_SERVICE_KEY}" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

This tells you which block just completed and how many weeks it ran.

STEP 2 — READ the review template:
  Read /Users/jarvisforoli/projects/ascent/openclaw/review-prompt.md
  Follow it as your master instructions for the review structure.

STEP 3 — PULL all data for the completed block from Supabase (source .env first). Calculate the date range from block start to today:
  - planned_workouts for the full block period
  - activities for the same window
  - exercise_progression across the block
  - sleep, hrv, body_battery, training_readiness for the full block
  - coaching_log entries (all adjustments, exceptions, decisions)
  - weekly_coaching_summary rows for all weeks in the block
  - stall_early_warning (current snapshot)
  - athlete_response_patterns (all learned patterns)
  - coaching_decision_outcomes (decision quality across the block)
  - exercise_feedback_trends (feel distribution per exercise)
  - sleep_performance_correlation (personal sleep → performance data)

STEP 4 — PRESENT the full analysis per review-prompt.md structure. Be thorough.

STEP 5 — POST a notification to #ascent-training (C0AQ1KJAKM0):
  TOKEN=$(cat ~/.openclaw/slack-bot-token)
  MSG="📊 Block review ready — open Claude Code Desktop → Scheduled → block-review to join the analysis and discuss next block planning."
  PAYLOAD=$(jq -Rn --arg c "C0AQ1KJAKM0" --arg t "$MSG" '{channel:$c, text:$t, mrkdwn:true}')
  curl -s -X POST https://slack.com/api/chat.postMessage \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "$PAYLOAD"

STEP 6 — End with: "Block analysis complete. Ready for your input on the next block — what direction do you want to take it?" Then stop. The user will join this session to discuss interactively.

DO NOT post the full analysis to Slack. Interactive discussion happens in this CCD session. Slack only gets the "ready" notification.
