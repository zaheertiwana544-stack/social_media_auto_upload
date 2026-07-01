import os

import yt_dlp

import config


def download_video(video_id: str, url: str) -> str:
    """Download a video by ID/URL, return the path to the resulting mp4 file."""
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    output_template = os.path.join(config.DOWNLOAD_DIR, f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": (
            "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]"
            "/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        ),
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    if config.YTDLP_COOKIES_FILE and os.path.exists(config.YTDLP_COOKIES_FILE):
        ydl_opts["cookiefile"] = config.YTDLP_COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    expected_path = os.path.join(config.DOWNLOAD_DIR, f"{video_id}.mp4")
    if not os.path.exists(expected_path):
        raise RuntimeError(f"Download finished but expected file not found: {expected_path}")

    return expected_path
