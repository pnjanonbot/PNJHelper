import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")

# Admin configuration
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
if not ADMIN_USER_ID:
    raise ValueError("ADMIN_USER_ID is not set in .env")

try:
    ADMIN_USER_ID = int(ADMIN_USER_ID)
except ValueError:
    raise ValueError("ADMIN_USER_ID must be an integer")

# Chat configuration
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT", 300))  # Default 5 minutes
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", 10))  # Default max 10 users in queue