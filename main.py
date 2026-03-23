import base64
import json
import logging
import re

import httpx
import sendgrid
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import Response
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

import config
from claude_service import process_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Schedule Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# SMS / MMS  (Twilio)
# ─────────────────────────────────────────────────────────────────────────────


def _send_sms(to: str, body: str) -> None:
    client = TwilioClient(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    client.messages.create(body=body, from_=config.TWILIO_PHONE_NUMBER, to=to)


def _handle_sms(body: str, from_number: str, media_items: list[tuple[str, str]]) -> None:
    """Background task: download MMS images, call Claude, send SMS reply."""
    images = []
    with httpx.Client(timeout=30) as client:
        for url, ctype in media_items:
            try:
                resp = client.get(
                    url,
                    auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN),
                )
                resp.raise_for_status()
                images.append({
                    "media_type": ctype,
                    "data": base64.standard_b64encode(resp.content).decode(),
                })
            except Exception as e:
                logger.warning("Failed to download MMS media from %s: %s", url, e)

    try:
        reply = process_message(body, images)
    except Exception as e:
        logger.error("Error processing SMS: %s", e)
        reply = "Sorry, something went wrong. Please try again."

    _send_sms(from_number, reply)


@app.post("/webhook/sms")
async def sms_webhook(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()

    body = form.get("Body", "")
    from_number = form.get("From", "")
    num_media = int(form.get("NumMedia", 0) or 0)

    media_items = [
        (form.get(f"MediaUrl{i}", ""), form.get(f"MediaContentType{i}", "image/jpeg"))
        for i in range(num_media)
        if form.get(f"MediaUrl{i}") and (form.get(f"MediaContentType{i}", "") or "").startswith("image/")
    ]

    background_tasks.add_task(_handle_sms, body, from_number, media_items)

    # Acknowledge Twilio immediately; the actual reply is sent via REST API
    twiml = MessagingResponse()
    return Response(content=str(twiml), media_type="application/xml")


# ─────────────────────────────────────────────────────────────────────────────
# Email  (SendGrid Inbound Parse)
# ─────────────────────────────────────────────────────────────────────────────


def _send_email(to: str, subject: str, body: str) -> None:
    sg = sendgrid.SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
    message = Mail(
        from_email=config.REPLY_EMAIL_FROM,
        to_emails=to,
        subject=subject,
        plain_text_content=body,
    )
    sg.send(message)


def _strip_html(html: str) -> str:
    """Very basic HTML tag stripper."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _parse_from_address(from_header: str) -> str:
    """Extract plain email from 'Name <email@example.com>' format."""
    if "<" in from_header:
        return from_header.split("<")[-1].rstrip(">").strip()
    return from_header.strip()


def _handle_email(text: str, from_email: str, subject: str, images: list) -> None:
    """Background task: call Claude, send email reply."""
    try:
        reply = process_message(text, images)
    except Exception as e:
        logger.error("Error processing email: %s", e)
        reply = "Sorry, something went wrong processing your request. Please try again."

    if not from_email:
        logger.warning("No from_email — cannot send reply")
        return

    reply_subject = subject if subject.startswith("Re:") else f"Re: {subject}"
    _send_email(to=from_email, subject=reply_subject, body=reply)


@app.post("/webhook/email")
async def email_webhook(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()

    logger.info("SendGrid fields: %s", list(form.keys()))
    logger.info("SendGrid from: %r", form.get("from", ""))
    logger.info("SendGrid sender: %r", form.get("sender", ""))

    from_header = form.get("from", "") or form.get("sender", "")
    subject = form.get("subject", "No subject")
    text_body = form.get("text", "") or _strip_html(form.get("html", ""))

    if subject:
        text_body = f"Subject: {subject}\n\n{text_body}"

    from_email = _parse_from_address(from_header)

    # Parse image attachments from SendGrid Inbound Parse multipart data
    images = []
    num_attachments = int(form.get("attachments", 0) or 0)
    attachments_meta: dict = {}
    try:
        attachments_meta = json.loads(form.get("attachment-info", "{}") or "{}")
    except json.JSONDecodeError:
        pass

    for i in range(1, num_attachments + 1):
        key = f"attachment{i}"
        meta = attachments_meta.get(key, {})
        ctype = meta.get("type", "")

        if not ctype.startswith("image/"):
            continue

        file_obj = form.get(key)
        if file_obj is None:
            continue

        try:
            content = await file_obj.read() if hasattr(file_obj, "read") else str(file_obj).encode()
            images.append({
                "media_type": ctype,
                "data": base64.standard_b64encode(content).decode(),
            })
        except Exception as e:
            logger.warning("Failed to read attachment %s: %s", key, e)

    background_tasks.add_task(_handle_email, text_body, from_email, subject, images)
    return {"status": "ok"}
