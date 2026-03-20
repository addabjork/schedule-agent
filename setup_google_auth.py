#!/usr/bin/env python3
"""
Run this script ONCE to authorize Google Calendar access.

It opens a browser window for you to sign in with your Google account,
then saves the credentials to token.json.

Steps before running:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or select one)
  3. Enable the Google Calendar API
  4. Go to APIs & Services > Credentials
  5. Create OAuth 2.0 credentials (Application type: Desktop app)
  6. Download the JSON file and save it as credentials.json in this directory

Then run:
  python setup_google_auth.py
"""

import json
import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"ERROR: {CREDENTIALS_PATH} not found.")
        print(__doc__)
        return

    print("Opening browser for Google authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"\nSuccess! Credentials saved to {TOKEN_PATH}")
    print("\n" + "=" * 60)
    print("For cloud deployments (Railway / Render), set this")
    print("as the GOOGLE_TOKEN_JSON environment variable:")
    print("=" * 60)
    print(open(TOKEN_PATH).read())


if __name__ == "__main__":
    main()
