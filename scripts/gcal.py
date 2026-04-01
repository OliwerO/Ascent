#!/usr/bin/env python3
"""Google Calendar CLI for Jarvis.

Usage:
  gcal.py list [--days N]                          List events for next N days (default 7)
  gcal.py create "Title" "2026-04-02T19:00" [--duration 60] [--description "..."] [--color N]
  gcal.py create-allday "Title" "2026-04-27" [--description "..."]
  gcal.py update EVENT_ID [--title "..."] [--start "..."] [--duration N] [--description "..."]
  gcal.py delete EVENT_ID
  gcal.py search "query" [--days N]

Colors: 1=Lavender 2=Sage 3=Grape 4=Flamingo 5=Banana 6=Tangerine 7=Peacock 8=Graphite 9=Blueberry 10=Basil 11=Tomato
"""

import sys
import json
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TIMEZONE = "Europe/Vienna"
CALENDAR_ID = "primary"

TOKEN_PATH = Path.home() / ".config" / "google-calendar-mcp" / "tokens.json"
CREDS_PATH = Path.home() / ".openclaw" / "workspace" / "openclaw" / "gcp-oauth.keys.json"


def get_credentials():
    with open(CREDS_PATH) as f:
        creds_data = json.load(f)["installed"]

    with open(TOKEN_PATH) as f:
        token_data = json.load(f)["normal"]

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=["https://www.googleapis.com/auth/calendar"],
    )

    if creds.expired:
        creds.refresh(Request())
        # Save refreshed token back
        token_data["access_token"] = creds.token
        token_data["expiry_date"] = int(creds.expiry.timestamp() * 1000) if creds.expiry else None
        with open(TOKEN_PATH) as f:
            all_tokens = json.load(f)
        all_tokens["normal"] = token_data
        with open(TOKEN_PATH, "w") as f:
            json.dump(all_tokens, f, indent=2)

    return creds


def get_service():
    return build("calendar", "v3", credentials=get_credentials())


def cmd_list(args):
    service = get_service()
    now = datetime.now(timezone(timedelta(hours=2)))  # CEST
    time_min = now.isoformat()
    time_max = (now + timedelta(days=args.days)).isoformat()

    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        timeZone=TIMEZONE,
    ).execute()

    events = result.get("items", [])
    if not events:
        print("No events found.")
        return

    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        summary = e.get("summary", "(no title)")
        eid = e["id"]
        print(f"{start}  {summary}  [id:{eid}]")


def cmd_create(args):
    service = get_service()
    start_dt = datetime.fromisoformat(args.start)
    end_dt = start_dt + timedelta(minutes=args.duration)

    event = {
        "summary": args.title,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
    }
    if args.description:
        event["description"] = args.description
    if args.color:
        event["colorId"] = str(args.color)

    result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"Created: {result['summary']} | {result['start']['dateTime']} | id:{result['id']}")


def cmd_create_allday(args):
    service = get_service()
    event = {
        "summary": args.title,
        "start": {"date": args.date},
        "end": {"date": args.date},
    }
    if args.description:
        event["description"] = args.description

    result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"Created all-day: {result['summary']} | {result['start']['date']} | id:{result['id']}")


def cmd_update(args):
    service = get_service()
    event = service.events().get(calendarId=CALENDAR_ID, eventId=args.event_id).execute()

    if args.title:
        event["summary"] = args.title
    if args.description:
        event["description"] = args.description
    if args.start:
        start_dt = datetime.fromisoformat(args.start)
        duration = args.duration or 60
        end_dt = start_dt + timedelta(minutes=duration)
        event["start"] = {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE}
        event["end"] = {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE}

    result = service.events().update(calendarId=CALENDAR_ID, eventId=args.event_id, body=event).execute()
    print(f"Updated: {result['summary']} | id:{result['id']}")


def cmd_delete(args):
    service = get_service()
    service.events().delete(calendarId=CALENDAR_ID, eventId=args.event_id).execute()
    print(f"Deleted event: {args.event_id}")


def cmd_search(args):
    service = get_service()
    now = datetime.now(timezone(timedelta(hours=2)))
    time_min = now.isoformat()
    time_max = (now + timedelta(days=args.days)).isoformat()

    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        q=args.query,
        singleEvents=True,
        orderBy="startTime",
        timeZone=TIMEZONE,
    ).execute()

    events = result.get("items", [])
    if not events:
        print("No matching events.")
        return

    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        summary = e.get("summary", "(no title)")
        print(f"{start}  {summary}  [id:{e['id']}]")


def main():
    parser = argparse.ArgumentParser(description="Google Calendar CLI for Jarvis")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List upcoming events")
    p_list.add_argument("--days", type=int, default=7)

    p_create = sub.add_parser("create", help="Create a timed event")
    p_create.add_argument("title")
    p_create.add_argument("start", help="ISO datetime, e.g. 2026-04-02T19:00")
    p_create.add_argument("--duration", type=int, default=60, help="Duration in minutes")
    p_create.add_argument("--description", default=None)
    p_create.add_argument("--color", type=int, default=None)

    p_allday = sub.add_parser("create-allday", help="Create an all-day event")
    p_allday.add_argument("title")
    p_allday.add_argument("date", help="YYYY-MM-DD")
    p_allday.add_argument("--description", default=None)

    p_update = sub.add_parser("update", help="Update an event")
    p_update.add_argument("event_id")
    p_update.add_argument("--title", default=None)
    p_update.add_argument("--start", default=None)
    p_update.add_argument("--duration", type=int, default=None)
    p_update.add_argument("--description", default=None)

    p_delete = sub.add_parser("delete", help="Delete an event")
    p_delete.add_argument("event_id")

    p_search = sub.add_parser("search", help="Search events")
    p_search.add_argument("query")
    p_search.add_argument("--days", type=int, default=30)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "list": cmd_list,
        "create": cmd_create,
        "create-allday": cmd_create_allday,
        "update": cmd_update,
        "delete": cmd_delete,
        "search": cmd_search,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
