import json
import logging
from datetime import date

import anthropic

import config
from calendar_service import create_event

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "name": "create_calendar_event",
        "description": "Create a Google Calendar event and send invites to attendees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title/name",
                },
                "start_datetime": {
                    "type": "string",
                    "description": (
                        "Start date/time in ISO 8601 format. "
                        "Use '2024-03-15T14:00:00' for timed events, "
                        "'2024-03-15' for all-day events."
                    ),
                },
                "end_datetime": {
                    "type": "string",
                    "description": (
                        "End date/time in ISO 8601 format, same format as start_datetime. "
                        "If not specified, default to 1 hour after start."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Event description or additional details",
                },
                "location": {
                    "type": "string",
                    "description": "Event location or address",
                },
                "invite_husband": {
                    "type": "boolean",
                    "description": (
                        "Whether to invite the husband. Default is true. "
                        "Only set to false if the user explicitly says "
                        "'just for me', 'only me', or similar."
                    ),
                },
            },
            "required": ["title", "start_datetime", "end_datetime"],
        },
    }
]


def process_message(text: str, images: list[dict]) -> str:
    """
    Process a message through Claude, extract event details, and create
    calendar events via tool use.

    images: list of {"media_type": "image/jpeg", "data": "<base64-string>"}
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    today = date.today().isoformat()

    system_prompt = f"""You are a helpful assistant that manages a family calendar.

Today's date is {today}.

When given a message, screenshot, or flyer about an event, extract the details \
and create a calendar event using the create_calendar_event tool.

Rules:
- The user's email is {config.USER_EMAIL} and her husband's email is {config.HUSBAND_EMAIL}
- By DEFAULT, invite BOTH the user and her husband (invite_husband=true)
- Only set invite_husband=false if the user explicitly says "just for me", \
"only me", "don't invite [name]", or similar
- If the end time isn't specified, default to 1 hour after start
- If the year is ambiguous, use the nearest future occurrence
- After creating the event, reply with a brief, friendly confirmation

If the message is not about a calendar event, respond helpfully without \
creating an event."""

    # Build message content — images first, then text
    content: list[dict] = []
    for img in images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img["media_type"],
                "data": img["data"],
            },
        })
    if text.strip():
        content.append({"type": "text", "text": text})

    if not content:
        return "I didn't receive any content. Please send a message or image."

    messages = [{"role": "user", "content": content}]

    # Agentic loop: keep going until Claude stops calling tools
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return "Done."

        if response.stop_reason != "tool_use":
            logger.warning("Unexpected stop_reason: %s", response.stop_reason)
            break

        # Append assistant turn, then execute each tool call
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "create_calendar_event":
                try:
                    result = create_event(
                        title=block.input["title"],
                        start_datetime=block.input["start_datetime"],
                        end_datetime=block.input["end_datetime"],
                        description=block.input.get("description", ""),
                        location=block.input.get("location", ""),
                        invite_husband=block.input.get("invite_husband", True),
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
                except Exception as e:
                    logger.error("create_event failed: %s", e)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error creating event: {e}",
                        "is_error": True,
                    })

        messages.append({"role": "user", "content": tool_results})

    return "Something went wrong processing your request. Please try again."
