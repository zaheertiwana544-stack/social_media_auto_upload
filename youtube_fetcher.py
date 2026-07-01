import re

from googleapiclient.discovery import build

import config

_DURATION_RE = re.compile(
    r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
)


def _parse_iso8601_duration(duration: str) -> int:
    match = _DURATION_RE.fullmatch(duration)
    if not match:
        return 0
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _client():
    return build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)


def _get_uploads_playlist_id(youtube, handle: str) -> str:
    response = youtube.channels().list(part="contentDetails", forHandle=handle).execute()
    items = response.get("items", [])
    if not items:
        raise RuntimeError(f"No YouTube channel found for handle: {handle}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_latest_video():
    """Return the channel's single most recent upload, as a 0- or 1-item list.

    No duration filter — both Shorts and long-form uploads qualify. This checks the
    latest video on every poll regardless of how long ago it was published, so a
    channel that posts weekly (or less often) is never missed by a time window.
    """
    youtube = _client()
    uploads_playlist_id = _get_uploads_playlist_id(youtube, config.YOUTUBE_CHANNEL_HANDLE)

    playlist_response = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=1,
    ).execute()

    items = playlist_response.get("items", [])
    if not items:
        return []

    video_id = items[0]["contentDetails"]["videoId"]

    videos_response = youtube.videos().list(
        part="contentDetails,snippet",
        id=video_id,
    ).execute()

    video_items = videos_response.get("items", [])
    if not video_items:
        return []

    item = video_items[0]
    duration_seconds = _parse_iso8601_duration(item["contentDetails"]["duration"])

    return [{
        "video_id": item["id"],
        "title": item["snippet"]["title"],
        "published_at": item["snippet"]["publishedAt"],
        "duration_seconds": duration_seconds,
        "url": f"https://www.youtube.com/watch?v={item['id']}",
    }]
