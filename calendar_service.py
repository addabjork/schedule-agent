import json
import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials() -> Credentials:
    creds = None

    # Prefer env var (cloud deployments) over file
    if config.GOOGLE_TOKEN_JSON:
        creds = Credentials.from_authorized_user_info(
            json.loads(config.GOOGLE_TOKEN_JSON), SCOPES
        )
    elif os.path.exists(config.GOOGLE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.GOOGLE_TOKEN_PATH, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Persist refreshed token back to file (local only; cloud uses env var)
        if not config.GOOGLE_TOKEN_JSON and os.path.exists(config.GOOGLE_TOKEN_PATH):
            with open(config.GOOGLE_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

    if not creds or not creds.valid:
        raise RuntimeError(
            "Google Calendar is not authenticated. "
            "Run setup_google_auth.py to authorize access."
        )

    return creds


def create_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    invite_husband: bool = True,
) -> dict:
    """Create a Google Calendar event and return its details."""
    service = build("calendar", "v3", credentials=_get_credentials())

    attendees = [{"email": config.USER_EMAIL}]
    if invite_husband:
        attendees.append({"email": config.HUSBAND_EMAIL})

    # Detect all-day events: date-only strings like "2024-03-15"
    is_all_day = "T" not in start_datetime and len(start_datetime) == 10

    if is_all_day:
        start = {"date": start_datetime[:10]}
        end = {"date": end_datetime[:10]}
    else:
        # Add timezone if none is specified
        has_tz = "+" in start_datetime or "Z" in start_datetime
        start = {"dateTime": start_datetime} if has_tz else {"dateTime": start_datetime, "timeZone": config.TIMEZONE}

        has_tz = "+" in end_datetime or "Z" in end_datetime
        end = {"dateTime": end_datetime} if has_tz else {"dateTime": end_datetime, "timeZone": config.TIMEZONE}

    event_body = {
        "summary": title,
        "description": description,
        "location": location,
        "start": start,
        "end": end,
        "attendees": attendees,
        "reminders": {"useDefault": True},
    }

    event = service.events().insert(
        calendarId="primary",
        body=event_body,
        sendUpdates="all",  # sends email invites to attendees
    ).execute()

    logger.info("Created event: %s (%s)", title, event.get("id"))

    return {
        "success": True,
        "event_id": event.get("id"),
        "html_link": event.get("htmlLink"),
        "title": title,
        "start": start_datetime,
        "end": end_datetime,
        "invited": [a["email"] for a in attendees],
    }
