import os

import requests

import config

GRAPH_API_VERSION = "v19.0"
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB per transfer request


def upload_video(file_path: str, description: str) -> str:
    """Upload a video file to the configured Facebook Page via the resumable upload
    protocol (start/transfer/finish). Returns the Facebook video id.

    Resumable upload handles large, long-form files reliably, unlike a single-shot
    POST which hits Facebook's size limit on anything beyond a couple hundred MB.
    """
    url = f"https://graph-video.facebook.com/{GRAPH_API_VERSION}/{config.FACEBOOK_PAGE_ID}/videos"
    file_size = os.path.getsize(file_path)

    start_resp = requests.post(
        url,
        data={
            "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
            "upload_phase": "start",
            "file_size": file_size,
        },
        timeout=60,
    )
    if start_resp.status_code != 200:
        raise RuntimeError(f"Facebook upload start failed ({start_resp.status_code}): {start_resp.text}")

    start_data = start_resp.json()
    upload_session_id = start_data["upload_session_id"]
    video_id = start_data["video_id"]
    start_offset = int(start_data["start_offset"])
    end_offset = int(start_data["end_offset"])

    with open(file_path, "rb") as f:
        while start_offset != end_offset:
            f.seek(start_offset)
            chunk = f.read(min(CHUNK_SIZE, end_offset - start_offset))

            transfer_resp = requests.post(
                url,
                data={
                    "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
                    "upload_phase": "transfer",
                    "upload_session_id": upload_session_id,
                    "start_offset": start_offset,
                },
                files={"video_file_chunk": chunk},
                timeout=120,
            )
            if transfer_resp.status_code != 200:
                raise RuntimeError(
                    f"Facebook upload transfer failed ({transfer_resp.status_code}): {transfer_resp.text}"
                )

            transfer_data = transfer_resp.json()
            start_offset = int(transfer_data["start_offset"])
            end_offset = int(transfer_data["end_offset"])

    finish_resp = requests.post(
        url,
        data={
            "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
            "upload_phase": "finish",
            "upload_session_id": upload_session_id,
            "description": description,
        },
        timeout=60,
    )
    if finish_resp.status_code != 200:
        raise RuntimeError(f"Facebook upload finish failed ({finish_resp.status_code}): {finish_resp.text}")

    finish_data = finish_resp.json()
    if not finish_data.get("success"):
        raise RuntimeError(f"Facebook upload finish did not report success: {finish_data}")

    return video_id
