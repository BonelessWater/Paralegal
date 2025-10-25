import os, json, requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.transport.requests import Request

load_dotenv()

SPACE_ID = os.getenv("SPACE_ID")                  # e.g., spaces/AAAA9vHkK2A
SA_KEY_PATH = os.getenv("GOOGLE_SA_KEY", "service_account.json")

SCOPES = ["https://www.googleapis.com/auth/chat.bot"]

creds = service_account.Credentials.from_service_account_file(
    SA_KEY_PATH, scopes=SCOPES
)
creds.refresh(Request())                          # fetch access token
token = creds.token

url = f"https://chat.googleapis.com/v1/{SPACE_ID}/messages"
payload = {"text": "Hello from my service account 🚀"}

resp = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json=payload,
    timeout=15,
)

if resp.ok:
    print("✅ Sent:", resp.json().get("name"))
else:
    print("❌ Failed:", resp.status_code, resp.text)
