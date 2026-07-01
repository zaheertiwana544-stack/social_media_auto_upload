# YouTube -> Facebook Auto-Uploader

Watches a YouTube channel for new uploads (Shorts and long-form alike), downloads them
(capped at 720p), and uploads them to a Facebook Page. Keeps a local SQLite database
(`state.db`) of every video it has seen so it never downloads or uploads the same video
twice.

Only run this against channels you have explicit permission/license to repost.

## 1. Install dependencies

```
pip install -r requirements.txt
```

ffmpeg must also be installed and on your PATH (already detected on this machine).

## 2. Get a YouTube Data API key

1. Go to https://console.cloud.google.com/
2. Create a project (or use an existing one).
3. APIs & Services -> Library -> enable "YouTube Data API v3".
4. APIs & Services -> Credentials -> Create Credentials -> API key.
5. Copy the key into `.env` as `YOUTUBE_API_KEY`.

The API has a free daily quota (10,000 units/day) which is more than enough for polling
one channel every 15 minutes.

## 3. Get a Facebook Page Access Token

1. Go to https://developers.facebook.com/apps and create an App (type: Business).
2. Add the "Facebook Login for Business" or just use Graph API Explorer:
   https://developers.facebook.com/tools/explorer
3. In Graph API Explorer: select your App, select your Page, and request these
   permissions: `pages_manage_posts`, `pages_read_engagement`, `publish_video`.
4. Generate a User Access Token, then exchange it for a long-lived one:
   ```
   GET https://graph.facebook.com/v19.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={app-id}
     &client_secret={app-secret}
     &fb_exchange_token={short-lived-user-token}
   ```
5. Use that long-lived user token to get a **Page** Access Token (these don't expire
   as long as the user token stays valid):
   ```
   GET https://graph.facebook.com/v19.0/me/accounts?access_token={long-lived-user-token}
   ```
   Find your Page in the response and copy its `access_token` and `id`.
6. Put those into `.env` as `FACEBOOK_PAGE_ACCESS_TOKEN` and `FACEBOOK_PAGE_ID`.

## 4. Configure

Copy `.env.example` to `.env` and fill in:

- `YOUTUBE_API_KEY`
- `YOUTUBE_CHANNEL_HANDLE` (e.g. `@SomeChannel` — from the channel's YouTube URL)
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

Adjust `POLL_INTERVAL_MINUTES` as needed.

Each poll cycle checks only the channel's single most recent upload (not a time
window) — if it hasn't been processed yet, it's downloaded and posted, regardless of
its length.

## 5. Run

```
python main.py
```

This runs forever: checks the channel, downloads the latest upload if it's not already
in `state.db`, uploads it to the Facebook Page (using Facebook's resumable/chunked
upload, so long-form videos work too), and records the result. It sleeps
`POLL_INTERVAL_MINUTES` between cycles.

## Duplicate protection

Every video is keyed by its YouTube video ID in `state.db`:

- Already `uploaded` -> skipped entirely (no re-download, no re-upload).
- Already `downloaded` but not uploaded (e.g. crashed mid-run) -> reuses the existing
  file instead of re-downloading, then retries the upload.
- `failed` -> retried on the next cycle.

## Running 24/7 on GitHub Actions (recommended free option)

No VPS, no card, no account approval — just a free GitHub account. Instead of one
process running forever, GitHub runs `run_once.py` (one check-and-upload cycle) on a
schedule, roughly every 15 minutes, and stores dedup state (`state.db`) back in the
repo between runs.

### 1. Create a GitHub repo and push this project

This folder already has its own git repo (separate from any other repo higher up in
your filesystem). From this project folder:
```
git add -A
git commit -m "Initial commit"
```
Then on github.com, create a new repo (public is fine — no secrets are ever stored in
the code, only in GitHub's encrypted Secrets, see below). Then:
```
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

### 2. Add your secrets

On the repo page: **Settings -> Secrets and variables -> Actions -> New repository
secret**. Add these four, using the same values from your local `.env`:
- `YOUTUBE_API_KEY`
- `YOUTUBE_CHANNEL_HANDLE`
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

### 2b. Add YouTube cookies (required — GitHub's IPs get bot-blocked otherwise)

YouTube blocks anonymous video downloads from cloud/data-center IPs (including
GitHub Actions runners) with a "confirm you're not a bot" challenge. The fix is to
give yt-dlp cookies from a real, logged-in browser session:

1. In Chrome or Firefox, log into youtube.com with any Google account.
2. Install a "cookies.txt" export extension, e.g. **"Get cookies.txt LOCALLY"**
   (search your browser's extension store).
3. While on a youtube.com tab, use the extension to export cookies for the site —
   it gives you the contents of a `cookies.txt` file (Netscape format).
4. Add a new repo secret named `YOUTUBE_COOKIES` and paste the **entire contents**
   of that file as the value.

These cookies can occasionally expire (e.g. if you log out, change password, or the
session naturally times out) — if uploads start failing again with a "Sign in to
confirm you're not a bot" error in the Actions logs, just re-export and update the
`YOUTUBE_COOKIES` secret.

### 3. Allow the workflow to commit state back

**Settings -> Actions -> General -> Workflow permissions** -> select **"Read and
write permissions"** -> Save. Without this, the workflow can run but can't save
dedup state between runs, and would re-process the same video every time.

### 4. Verify

Go to the **Actions** tab -> "YouTube to Facebook auto-upload" -> **Run workflow** to
trigger it manually the first time. Check the run's logs to confirm it completes.
After that, it runs automatically on the `*/15 * * * *` schedule defined in
`.github/workflows/auto_upload.yml` — no PC or server of yours needs to stay on.

Note: GitHub may delay scheduled runs by a few minutes under high platform load —
this is normal and fine for this use case.

## Running 24/7 on Oracle Cloud Free Tier (alternative, if you get access working)

Oracle Cloud's "Always Free" tier includes a small Linux VM with no time limit, at no
cost. Steps:

### 1. Create the VM (done in your browser, not here)

1. Sign up at https://www.oracle.com/cloud/free/ (requires a card for identity
   verification, but the Always Free resources stay free indefinitely).
2. Console -> Compute -> Instances -> **Create Instance**.
3. Image: **Ubuntu** (latest LTS). Shape: pick one under "Always Free eligible" —
   either the Ampere A1 (ARM) or `VM.Standard.E2.1.Micro` (AMD) shape.
4. Add your SSH key when creating the instance (or generate one — Oracle's UI can do
   this and gives you a `.key` file to download). Create the instance and note its
   **public IP**.

### 2. Get code onto the VM

From your Windows machine, SSH in first to confirm access:
```
ssh -i /path/to/your-key.key ubuntu@<VM_PUBLIC_IP>
```

Then copy the project over (run this from this project folder on Windows, in a
separate terminal):
```
scp -i /path/to/your-key.key -r "c:\Users\Tiwana\Desktop\social_media_auto_upload" ubuntu@<VM_PUBLIC_IP>:/tmp/app
```

On the VM:
```
sudo mkdir -p /opt/social_media_auto_upload
sudo mv /tmp/app/* /opt/social_media_auto_upload/
sudo chown -R ubuntu:ubuntu /opt/social_media_auto_upload
```

Your local `.env` is excluded from most transfers by `.gitignore` but `scp -r` copies
everything including it — that's fine here since it's a direct machine-to-machine
copy, not a public upload. Just don't commit `.env` to any git repo.

### 3. Run the setup script

On the VM:
```
cd /opt/social_media_auto_upload
chmod +x deploy/setup_vps.sh
```

The service file assumes the default Oracle Ubuntu username `ubuntu`. If yours is
different, edit the `User=` line in `deploy/social-media-auto-upload.service` first.
Then run:
```
./deploy/setup_vps.sh
```

This installs Python/ffmpeg, creates a virtualenv, installs dependencies, and sets up
a systemd service that auto-restarts on crash or VM reboot.

### 4. Verify

```
sudo systemctl status social-media-auto-upload
sudo journalctl -u social-media-auto-upload -f
```

You should see the same "Starting auto-upload loop..." log line as when running it
locally. From here it runs continuously — no PC needs to stay on.
