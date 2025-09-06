import os
import json

# Telegram bot token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = "ecebot"

# Google Drive (Service Account only, no personal Drive folder needed)
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

if GOOGLE_SERVICE_ACCOUNT_JSON:
    GOOGLE_CREDS = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
else:
    GOOGLE_CREDS = None

# Admin IDs (comma separated in env var)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Auto approve toggle (for dev)
AUTO_APPROVE = os.environ.get("AUTO_APPROVE", "false").lower() == "true"
