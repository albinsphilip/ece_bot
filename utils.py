import urllib.parse
import urllib.request
import json
import config

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def parse_update(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")
    document = message.get("document")
    return chat_id, text, document

def trigger_worker(job_id: str):
    """
    Self-invokes the worker endpoint on Vercel to process a job in background.
    """
    if not config.BASE_URL or not config.INTERNAL_API_TOKEN:
        return False

    url = f"{config.BASE_URL}/api/worker"
    payload = json.dumps({"job_id": job_id}).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.INTERNAL_API_TOKEN}"
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            _ = resp.read()
            return True
    except Exception:
        # Even if trigger fails, the request may have reached—logs will help debug.
        return False
