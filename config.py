import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
GOOGLE_TOKEN_JSON = os.getenv("GOOGLE_TOKEN_JSON", "")  # For cloud deployments

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
REPLY_EMAIL_FROM = os.getenv("REPLY_EMAIL_FROM", "")

USER_EMAIL = os.environ["USER_EMAIL"]
HUSBAND_EMAIL = os.environ["HUSBAND_EMAIL"]

TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
HOME_ADDRESS = os.getenv("HOME_ADDRESS", "")
TRAVEL_MODE = os.getenv("TRAVEL_MODE", "transit")
