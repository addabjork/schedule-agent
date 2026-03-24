import logging
from datetime import datetime

import httpx

import config

logger = logging.getLogger(__name__)

GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def get_transit_duration_minutes(destination: str, arrival_datetime: str) -> int | None:
    """
    Get transit travel time from home to destination in minutes.
    Uses NYC subway/public transit.
    Returns None if location can't be geocoded or the API fails.
    """
    params = {
        "origin": config.HOME_ADDRESS,
        "destination": destination,
        "mode": "transit",
        "key": config.GOOGLE_MAPS_API_KEY,
    }

    # Pass arrival_time so Google picks realistic subway schedules
    try:
        dt = datetime.fromisoformat(arrival_datetime)
        params["arrival_time"] = int(dt.timestamp())
    except (ValueError, OSError):
        pass  # fall back to current time if parsing fails

    try:
        resp = httpx.get(GOOGLE_MAPS_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Maps API request failed: %s", e)
        return None

    if data.get("status") != "OK" or not data.get("routes"):
        logger.warning("Maps API returned status: %s", data.get("status"))
        return None

    duration_seconds = data["routes"][0]["legs"][0]["duration"]["value"]
    return duration_seconds // 60
