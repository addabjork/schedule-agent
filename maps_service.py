import logging
from datetime import datetime

import httpx

import config

logger = logging.getLogger(__name__)

GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def get_travel_duration_minutes(
    destination: str, arrival_datetime: str, mode: str = "transit"
) -> int | None:
    """
    Get travel time from home to destination in minutes.
    Mode can be: transit, driving, walking, bicycling.
    Returns None if location can't be geocoded or the API fails.
    """
    params = {
        "origin": config.HOME_ADDRESS,
        "destination": destination,
        "mode": mode,
        "key": config.GOOGLE_MAPS_API_KEY,
    }

    # Pass arrival_time for transit so Google picks realistic schedules
    if mode == "transit":
        try:
            dt = datetime.fromisoformat(arrival_datetime)
            params["arrival_time"] = int(dt.timestamp())
        except (ValueError, OSError):
            pass

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
