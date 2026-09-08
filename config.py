import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        print(f"CRITICAL: Missing environment variable: {name}")
        sys.exit(1)

    return value


try:
    API_ID = int(get_required_env("API_ID"))
except ValueError:
    print("CRITICAL: API_ID must be a valid integer.")
    sys.exit(1)

API_HASH = get_required_env("API_HASH")
BOT_TOKEN = get_required_env("BOT_TOKEN")

# Optional for now.
# If the final voice-chat implementation requires it,
# we will make it mandatory.
SESSION_STRING = os.getenv("SESSION_STRING", "").strip()

DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db").strip()
