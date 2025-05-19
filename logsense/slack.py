import os, requests

_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")

def push(text: str):
    if not _WEBHOOK:
        return "no-webhook"
    try:
        requests.post(_WEBHOOK,
                      json={"text": text.strip()[:1000]},
                      timeout=5)
        return "sent"
    except Exception:
        return "failed"
