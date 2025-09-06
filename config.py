import os
import json

# Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = "ecebot"  # used only if your URI does not include a default DB

# Google Drive (Service Account only)
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_CREDS = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON) if GOOGLE_SERVICE_ACCOUNT_JSON else None

# Admins
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Flags
AUTO_APPROVE = os.environ.get("AUTO_APPROVE", "false").lower() == "true"

# Internal worker call (self-invocation)
INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
