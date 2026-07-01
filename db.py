import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    published_at TEXT,
    status TEXT NOT NULL DEFAULT 'seen',
    file_path TEXT,
    fb_post_id TEXT,
    error TEXT,
    seen_at TEXT NOT NULL,
    downloaded_at TEXT,
    uploaded_at TEXT
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.execute(SCHEMA)


def now():
    return datetime.now(timezone.utc).isoformat()


def is_known(video_id: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM videos WHERE video_id = ?", (video_id,)
        ).fetchone()
        return row is not None


def mark_seen(video_id: str, title: str, published_at: str):
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO videos (video_id, title, published_at, status, seen_at) "
            "VALUES (?, ?, ?, 'seen', ?)",
            (video_id, title, published_at, now()),
        )


def mark_downloaded(video_id: str, file_path: str):
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status = 'downloaded', file_path = ?, downloaded_at = ? "
            "WHERE video_id = ?",
            (file_path, now(), video_id),
        )


def mark_uploaded(video_id: str, fb_post_id: str):
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status = 'uploaded', fb_post_id = ?, uploaded_at = ? "
            "WHERE video_id = ?",
            (fb_post_id, now(), video_id),
        )


def mark_failed(video_id: str, error: str):
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status = 'failed', error = ? WHERE video_id = ?",
            (error, video_id),
        )


def get_status(video_id: str):
    with connect() as conn:
        row = conn.execute(
            "SELECT status, file_path FROM videos WHERE video_id = ?", (video_id,)
        ).fetchone()
        return row
