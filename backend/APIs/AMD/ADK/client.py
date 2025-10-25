# client.py
import os, requests
SERVER = "http://134.199.202.8:8080/prompt"
TOKEN  = os.getenv("PROMPT_AUTH", "changeme")
while True:
    p = input("> ")
    if p.lower() in {"exit","quit"}: break
    r = requests.post(SERVER, json={"prompt": p}, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
    print("Server:", r.json().get("response", r.text))
