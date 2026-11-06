# cPanel deployment and upgrade (Python 3.10+)

This guide upgrades an existing **working** cPanel backend without changing its cPanel app registration, credentials, or private media files.

## Before touching the working installation

1. Export a backup of your cPanel Python application's `cpanel_app.py`, `passenger_wsgi.py`, and `web-player` folder.
2. Preserve **all** current environment variables, especially `FPP_STREAM_TOKEN`, `FPP_PAIR_CODE`, `FPP_PUBLIC_URL`, and `FPP_STREAM_MEDIA`. Never share them with visitors or commit to GitHub.
3. Preserve the `private-media/` directory and its `state.sqlite3` database. **Do not overwrite, delete, or re-create them.**
4. If the existing installation works, update during a test period rather than during an active holiday show.

## Upload file locations

Through cPanel File Manager, overwrite **only** the program files:

| Release file | cPanel destination |
|---|---|
| `backend/cpanel_app.py` | `~/fpp-audio-backend/cpanel_app.py` |
| `backend/passenger_wsgi.py` | `~/fpp-audio-backend/passenger_wsgi.py` |
| `backend/requirements-cpanel.txt` | `~/fpp-audio-backend/requirements-cpanel.txt` |
| `web-player/index.html` | `~/web-player/index.html` |
| `web-player/player.js` | `~/web-player/player.js` |
| `web-player/styles.css` | `~/web-player/styles.css` |
| `web-player/donate-qr.png` | `~/web-player/donate-qr.png` |

This layout matches the original v0.4 deployment. The backend can also use a `web-player` folder inside the application root. **Do not** upload a nested `backend/` folder *inside* your existing Python application root.

Python app setup (existing): version 3.10+, root `fpp-audio-backend`, startup `passenger_wsgi.py`, WSGI entry `application`, application URL your public HTTPS subdomain.

Install or update requirements inside the existing Python app's virtual environment:

```bash
cd ~/fpp-audio-backend
pip install -r requirements-cpanel.txt
```

Restart from **cPanel → Setup Python App → Restart**. Do **not** run `backend/server.py`, install a systemd service on cPanel, or change the app root. Keep `private-media` outside public web roots.

## Developer contribution link

The free player always offers a voluntary developer-support panel linking to the project developer's Stripe-hosted contribution page. No donation is required to listen; card details are handled by Stripe, not this server. There is no cPanel setting to suppress this link. Visitors decide whether to open it or donate.

## Keep these old settings

`FPP_STREAM_TOKEN`, `FPP_PAIR_CODE`, `FPP_PUBLIC_URL`, `FPP_STREAM_MEDIA`, `FPP_MAX_MEDIA_BYTES`, and `FPP_STALE_SECONDS` are unchanged. You **do not need to pair your FPP device again** when replacing only code files.

## Verify after the restart

1. `https://YOUR-HOST/health` returns `{"ok":true,"version":"1.0.0-rc4-cpanel"}`.
2. `https://YOUR-HOST/api/player-config` returns developer-support options without any FPP device authentication secrets.
3. `https://YOUR-HOST/api/shows/fpp` returns active playback metadata when FPP is playing; expect `media_ready:true` once the MP3 has uploaded.
4. `https://YOUR-HOST/listen/fpp/` loads the new player (including CSS/JS), and a phone on cellular data plays music when **Listen live** is tapped.
5. Open the support panel. The direct donation link should target the same Stripe page as the provided QR. Do not complete a real payment just for testing.

## Troubleshooting

- **Old UI after upload:** clear cache / force refresh; the stylesheet and JavaScript have versioned asset URLs.
- **404 on listener:** missing `~/web-player/index.html` or files in the wrong directory.
- **404 on `donate-qr.png`:** copy `web-player/donate-qr.png` to the existing web-player folder.
- **Developer support link missing:** clear browser cache, ensure updated player.js is deployed, and verify `/api/player-config` is available. No Stripe JavaScript is embedded.
- **`media_ready:false`:** inspect the stored filename. The backend decodes `%20` back to spaces; older encoded filenames may require renaming once.
- **Pairing 403:** pairing needs HTTPS and the configured code; do not disable HTTPS checks.
- **PUT 413 or 403:** hosting request body limit, quota, or WAF; check Passenger logs / ask the host.
- **No FPP logs:** verify agent service and file read permissions; the release agent now logs media uploads and HTTP response codes.
