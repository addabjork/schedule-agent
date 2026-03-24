# Schedule Agent

An AI-powered family scheduling assistant. Email or text it event details — plain text, flyers, screenshots, invitations — and it automatically creates Google Calendar events and invites everyone.

## Features

- **Email or SMS** — send events via email or text message, including images
- **Reads anything** — parses flyers, screenshots, and photos using Claude's vision
- **Invites your partner** — adds both you and a partner to every event by default; say "just for me" to skip
- **Travel buffer** — automatically checks travel time and adds a 🚗 travel block before events that require more than 15 minutes; configurable for transit, driving, walking, or cycling

## How it works

1. You email or text the agent with an event description or image
2. Claude extracts the event details (title, date, time, location)
3. A Google Calendar event is created with invites sent to you and your partner
4. If the event has a location, travel time is checked using Google Maps and a buffer block is added if needed
5. The agent replies confirming what was created

## Stack

- **Python** + FastAPI
- **Claude Opus 4.6** (Anthropic) — parses text and images, drives tool use
- **Google Calendar API** — creates events and sends invites
- **Google Maps Directions API** — estimates travel time (transit, driving, walking, or cycling)
- **SendGrid Inbound Parse** — receives emails
- **Twilio** — receives SMS/MMS
- **Railway** (or any PaaS) — hosts the server

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/schedule-agent.git
cd schedule-agent
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in all values in `.env` — see the section below for how to obtain each one.

### 3. Authorize Google Calendar

Download OAuth 2.0 credentials from Google Cloud Console (see below), save as `credentials.json`, then run:

```bash
python3 setup_google_auth.py
```

This opens a browser for you to authorize calendar access. The resulting `token.json` (or the `GOOGLE_TOKEN_JSON` env var for cloud deployments) is required for the app to create events.

### 4. Deploy

```bash
# Local
uvicorn main:app --reload

# Railway / Render — uses Procfile automatically
```

Set all env vars in your hosting platform's dashboard. For `GOOGLE_TOKEN_JSON`, paste the full contents of `token.json`.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | From [console.anthropic.com](https://console.anthropic.com) |
| `USER_EMAIL` | ✅ | Your Google account email |
| `PARTNER_EMAIL` | ✅ | Your partner's email (invited by default) |
| `TIMEZONE` | ✅ | IANA timezone, e.g. `America/New_York` |
| `GOOGLE_CREDENTIALS_PATH` | ✅ | Path to `credentials.json` (default: `credentials.json`) |
| `GOOGLE_TOKEN_PATH` | ✅ | Path to `token.json` (default: `token.json`) |
| `GOOGLE_TOKEN_JSON` | Cloud only | Full contents of `token.json` for cloud deployments |
| `GOOGLE_MAPS_API_KEY` | ✅ | For travel time estimates |
| `HOME_ADDRESS` | ✅ | Your home address, used as the travel origin |
| `TRAVEL_MODE` | ✅ | `transit`, `driving`, `walking`, or `bicycling` (default: `transit`) |
| `SENDGRID_API_KEY` | Email | From [sendgrid.com](https://sendgrid.com) |
| `REPLY_EMAIL_FROM` | Email | Address the agent replies from, e.g. `schedule@yourdomain.com` |
| `TWILIO_ACCOUNT_SID` | SMS | From [twilio.com](https://twilio.com) |
| `TWILIO_AUTH_TOKEN` | SMS | From Twilio dashboard |
| `TWILIO_PHONE_NUMBER` | SMS | Your Twilio number in `+1XXXXXXXXXX` format |

---

## Service Setup

### Google Cloud
1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **Google Calendar API** and **Directions API**
3. Create **OAuth 2.0 credentials** (Desktop app) → download as `credentials.json`
4. Create an **API key** for the Maps/Directions API → set as `GOOGLE_MAPS_API_KEY`

### SendGrid (Email)
1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Authenticate your domain under **Sender Authentication**
3. Add an MX record in your DNS: `your-subdomain` → `mx.sendgrid.net` (priority 10, DNS only)
4. Set up **Inbound Parse**: hostname `your-subdomain.yourdomain.com`, URL `https://your-app/webhook/email`
5. Email the agent at any address `@your-subdomain.yourdomain.com`

### Twilio (SMS)
1. Sign up at [twilio.com](https://twilio.com) and get a phone number
2. Under the number's settings, set the incoming message webhook to `https://your-app/webhook/sms` (HTTP POST)
3. Note: US carriers require 10DLC registration for MMS — register under **Messaging → A2P 10DLC**

---

## Usage

**Add an event by email:**
Send any email to your configured inbound address describing an event. Attach or paste a flyer image if you have one.

**Add an event by SMS:**
Text your Twilio number. Send an image of a flyer or just describe the event in plain text.

**Skip inviting your partner:**
Include "just for me" or "only me" in your message.

**Examples:**
- *"Dinner at Nobu on Friday April 3rd at 7:30pm"*
- *"Soccer practice Saturday 10am at Riverside Park"*
- *(photo of a birthday party invitation)*
- *"Doctor's appointment Monday at 2pm, just for me"*

---

## License

MIT
