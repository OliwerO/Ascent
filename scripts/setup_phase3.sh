#!/bin/bash
# Phase 3 Setup: Garmin MCP Server + OpenClaw Health Coach Skill
# Run this on the Mac where Jarvis/OpenClaw is running.

set -euo pipefail

echo "=== Phase 3: Garmin MCP + Health Coach Skill ==="

# 1. Install garmin-connect-mcp
echo ""
echo "--- Installing garmin-connect-mcp ---"
if command -v uvx &> /dev/null; then
    echo "uvx available, garmin-connect-mcp will run via uvx (no global install needed)"
else
    echo "Installing uv (for uvx)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Verify it can launch
echo "Testing garmin-connect-mcp..."
uvx --python 3.12 --from garmin-connect-mcp garmin-connect-mcp --help 2>/dev/null && echo "OK" || echo "Warning: garmin-connect-mcp test failed (may need auth)"

# 2. Deploy health-coach skill
SKILL_DIR="$HOME/.openclaw/workspace/skills/health-coach"
echo ""
echo "--- Deploying health-coach skill to $SKILL_DIR ---"
mkdir -p "$SKILL_DIR"
cp "$(dirname "$0")/../openclaw/skills/health-coach/SKILL.md" "$SKILL_DIR/SKILL.md"
echo "Skill deployed: $SKILL_DIR/SKILL.md"

# 3. Show MCP config to add to OpenClaw
echo ""
echo "--- OpenClaw MCP Config ---"
echo "Add the following to your openclaw.json under mcp_servers:"
echo ""
cat "$(dirname "$0")/../openclaw/garmin-mcp-config.json"
echo ""
echo "Make sure GARMIN_EMAIL and GARMIN_PASSWORD are set in your environment."

# 4. Create coaching context file
CONTEXT_DIR="$HOME/vault/second-brain/projects/ascent"
CONTEXT_FILE="$CONTEXT_DIR/coaching-context.md"
if [ ! -f "$CONTEXT_FILE" ]; then
    echo ""
    echo "--- Creating coaching-context.md ---"
    mkdir -p "$CONTEXT_DIR"
    cat > "$CONTEXT_FILE" << 'CTXEOF'
# Ascent Coaching Context

## Current Goals
<!-- Updated by coach and Opus -->

## Current Training Program
<!-- Set by Opus during interactive sessions -->

## Season Context
- Current season: Winter/Spring 2026
- Primary focus: Mountain sports (ski touring, splitboarding)
- Secondary: Gym maintenance

## Injury & Soreness Log
<!-- Coach logs here when user reports issues -->

## Learned Preferences
<!-- Coach adds observations about what works for Oliwer -->

## Coaching Decisions Log
<!-- Coach logs day-to-day adjustments with date and reason -->
CTXEOF
    echo "Created: $CONTEXT_FILE"
else
    echo "coaching-context.md already exists, skipping."
fi

echo ""
echo "=== Phase 3 setup complete ==="
echo ""
echo "Next steps:"
echo "1. Add the MCP config JSON to your openclaw.json"
echo "2. Restart OpenClaw gateway"
echo "3. Test: ask Jarvis 'how was my sleep last night?'"
echo "4. Verify skill visible in /context detail"
