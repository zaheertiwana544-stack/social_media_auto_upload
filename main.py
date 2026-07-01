import logging
import os
import time

import config
import db
import downloader
import facebook_uploader
import youtube_fetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("auto_upload")


def run_cycle():
    videos = youtube_fetcher.fetch_latest_video()
    if not videos:
        log.info("No videos found on channel")
        return

    for video in videos:
        video_id = video["video_id"]
        db.mark_seen(video_id, video["title"], video["published_at"])

        status_row = db.get_status(video_id)
        status = status_row[0] if status_row else "seen"

        if status == "uploaded":
            continue  # already posted to Facebook, skip entirely

        try:
            file_path = status_row[1] if status_row and status_row[1] else None
            if status != "downloaded" or not file_path or not os.path.exists(file_path):
                log.info("Downloading %s (%s)", video_id, video["title"])
                file_path = downloader.download_video(video_id, video["url"])
                db.mark_downloaded(video_id, file_path)

            log.info("Uploading %s to Facebook", video_id)
            fb_post_id = facebook_uploader.upload_video(file_path, video["title"])
            db.mark_uploaded(video_id, fb_post_id)
            log.info("Uploaded %s -> Facebook post %s", video_id, fb_post_id)

        except Exception as exc:
            log.exception("Failed processing %s: %s", video_id, exc)
            db.mark_failed(video_id, str(exc))


def main():
    db.init_db()
    log.info(
        "Starting auto-upload loop. Channel=%s, interval=%s min",
        config.YOUTUBE_CHANNEL_HANDLE,
        config.POLL_INTERVAL_MINUTES,
    )
    while True:
        try:
            run_cycle()
        except Exception:
            log.exception("Cycle failed, will retry next interval")
        time.sleep(config.POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
