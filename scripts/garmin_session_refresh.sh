#!/bin/bash
# Garmin session refresh — silently reloads Garmin Connect in Safari
# to keep the session cookie alive. Run every 4 hours via launchd.
#
# If Safari doesn't have a Garmin tab, opens one in the background.
# If Safari isn't running, does nothing (session refreshes on next Safari launch).

GARMIN_URL="https://connect.garmin.com/modern/"
LOG="/Users/jarvisforoli/projects/ascent/logs/session-refresh.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
}

# Check if Safari is running
if ! pgrep -q Safari; then
    log "Safari not running — skipping refresh"
    exit 0
fi

# Try to find and reload an existing Garmin tab, or open a new one
osascript <<'EOF' 2>/dev/null
tell application "Safari"
    set garminFound to false
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "connect.garmin.com" then
                set URL of t to "https://connect.garmin.com/modern/"
                set garminFound to true
                exit repeat
            end if
        end repeat
        if garminFound then exit repeat
    end repeat

    if not garminFound then
        -- Open Garmin in a new tab in the last window (least intrusive)
        if (count of windows) > 0 then
            tell last window
                set newTab to make new tab with properties {URL:"https://connect.garmin.com/modern/"}
            end tell
        end if
    end if
end tell
EOF

if [ $? -eq 0 ]; then
    log "Safari Garmin tab refreshed"
else
    log "Safari refresh failed"
fi

# Wait for page to load, then extract tokens
sleep 10

cd /Users/jarvisforoli/projects/ascent
source venv/bin/activate
python -c "
import browser_cookie3, requests, json, re
from pathlib import Path

TOKEN_FILE = Path('/Users/jarvisforoli/projects/ascent/garmin_tokens.json')

try:
    cj = browser_cookie3.safari(domain_name='garmin.com')
    jwt_web, cookie_dict = None, {}
    for c in cj:
        if 'garmin' in c.domain or 'connect' in c.domain:
            cookie_dict[c.name] = c.value
        if c.name == 'JWT_WEB':
            jwt_web = c.value

    if not jwt_web:
        print('No JWT found')
        exit(1)

    sess = requests.Session()
    for c in cj:
        sess.cookies.set(c.name, c.value, domain=c.domain, path=c.path)
    r = sess.get('https://connect.garmin.com/modern/', headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15',
    })
    match = re.search(r'<meta[^>]*csrf[^>]*content=\"([^\"]+)\"', r.text, re.IGNORECASE)
    csrf = match.group(1) if match else None

    if not csrf:
        print('No CSRF found')
        exit(1)

    TOKEN_FILE.write_text(json.dumps({
        'jwt_web': jwt_web,
        'csrf_token': csrf,
        'cookies': cookie_dict,
    }, indent=2))
    print(f'Tokens refreshed')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
" >> "$LOG" 2>&1

log "Token refresh complete"
