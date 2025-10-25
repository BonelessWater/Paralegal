import os
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
SPACE_ID = os.getenv("SPACE_ID")

# Your message payload
payload = {
    "text": "Hello from Python using GOOGLE_API_KEY 🚀"
}

# Google Chat API endpoint
url = f"https://chat.googleapis.com/v1/{SPACE_ID}/messages?key={API_KEY}"

response = requests.post(url, json=payload)

if response.status_code == 200:
    print("✅ Message sent successfully!")
else:
    print("❌ Failed:", response.status_code, response.text)
