import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


YOUTUBE_API_KEY = _require("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_HANDLE = _require("YOUTUBE_CHANNEL_HANDLE")

FACEBOOK_PAGE_ID = _require("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = _require("FACEBOOK_PAGE_ACCESS_TOKEN")

POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))

DB_PATH = os.getenv("DB_PATH", "state.db")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
