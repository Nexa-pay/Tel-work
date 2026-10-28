import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Reporting tuning
MAX_CONCURRENT_REPORTS = 5          # per task
REPORT_GAP_MIN = 2.0
REPORT_GAP_MAX = 5.0
ACCOUNT_ROTATION_DELAY = 15
PROXY_CHECK_TIMEOUT = 8
