# LightShow Web Stream — User Manual

**Release:** 1.0.0-rc2 (release candidate)  
**Compatible target:** Falcon Player (FPP) 10.x with the self-hosted Python 3.10+ / Flask / Passenger backend. Other versions and hosts may work but are not validated.

LightShow Web Stream lets visitors scan a QR code, open a mobile webpage, and listen to a show’s soundtrack over Wi-Fi or cellular data. An agent on the FPP controller periodically sends playback state and uploads the current audio file to your separate HTTPS backend. The server delivers the audio to visitors. Playback is **approximately** aligned to the lights; network latency, browser rules, and Bluetooth audio can cause delay.

## Contents

1. [What you need](#1-what-you-need)
2. [Install the backend on cPanel](#2-install-the-backend-on-cpanel)
3. [Install the FPP plugin](#3-install-the-fpp-plugin)
4. [Pair and configure](#4-pair-and-configure)
5. [Give visitors a listening link](#5-give-visitors-a-listening-link)
6. [Test the complete system](#6-test-the-complete-system)
7. [Optional developer support](#7-optional-developer-support)
8. [Troubleshooting](#8-troubleshooting)
9. [Updates and backups](#9-updates-and-backups)
10. [Privacy, security and media rights](#10-privacy-security-and-media-rights)

## 1. What you need

- An FPP 10.x controller with working Internet access and MP3 music under `/home/fpp/media/music/`.
- A public **HTTPS** Python 3.10+ server that can run Flask with writable private storage and receive audio-sized HTTP PUT requests. This package has been structured for cPanel’s Passenger/WSGI **Setup Python App** feature.
- A DNS name and TLS certificate for the backend. Visitors need access to that address through their own Internet connections.
- An SSH terminal for initial diagnostics, plus a cPanel account for uploads and environment variables.

FPP keeps running the light show if the streaming service is unavailable; remote audio listening will not work without network/server access.

## 2. Install the backend on cPanel

In **cPanel → Setup Python App**, create/select the existing application with Python 3.10+, root `fpp-audio-backend`, startup file `passenger_wsgi.py`, and callable `application`. Choose a publicly reachable HTTPS application URL.

Upload `backend/` **contents** to `~/fpp-audio-backend/`. Upload `web-player/` **contents** to `~/web-player/` (a sibling directory). Keep `private-media/`, `state.sqlite3`, and secrets unchanged during upgrades.

Install dependencies within the app's Python virtual environment:

```bash
cd ~/fpp-audio-backend
pip install -r requirements-cpanel.txt
```

The backend needs the following environment variables under cPanel’s Python-app settings:

| Name | Purpose |
|---|---|
| `FPP_STREAM_TOKEN` | Long random device authentication token; never publish it |
| `FPP_PAIR_CODE` | Random one-time setup code used by the FPP pairing screen |
| `FPP_PUBLIC_URL` | Public HTTPS base URL, such as `https://stream.example.com` |
| `FPP_STREAM_MEDIA` | Optional path to private audio storage; defaults to `private-media` below app root |
| `FPP_MAX_MEDIA_BYTES` | Optional maximum upload size, default 100 MiB |
| `FPP_STALE_SECONDS` | Optional maximum status-update age, default 12 s |

To create both credentials, run `python3 generate-secrets.py` from the backend folder and copy its output to the app environment variables. **Do not replace existing credentials on a paired installation.** Restart the Python app and visit `https://YOUR-HOST/health`; expect `ok: true`.

For a fuller hosting walkthrough, see [cPanel Deployment Guide](CPANEL-DEPLOY.md).

## 3. Install the FPP plugin

Open **FPP → Content Setup → Plugin Manager**. On FPP 10, select **Developer** under **FPP Settings → UI** if you need to install an unlisted GitHub plugin. In the available-plugins search field enter:

`https://github.com/c08oliverbrian/fpp-audio-preprocessed`

Install **LightShow Web Stream**. On systems with an existing version, use **Installed → Check for Updates / Update** instead of reinstalling. Plugin settings are stored separately from program files and should survive updates. Back them up before updating anyway.

## 4. Pair and configure

In FPP, open **Content Setup → LightShow Web Stream** or use:

`http://fpp.local/plugin.php?plugin=fpp-audio-preprocessed&page=content.php`

- **Enable audio synchronization agent:** checked.
- **Backend HTTPS URL:** `https://YOUR-HOST` (no trailing path).
- **Device ID:** short stable identifier such as `fpp`. It is part of the listener URL, but **is not displayed as a show title**.
- **Display name shown to visitors:** your preferred show name. If blank or the same as the Device ID, the player displays a generic light-show heading.
- **Pairing code:** enter the `FPP_PAIR_CODE` from cPanel and select **Save settings**. The device token should be stored automatically; do not put it in a public webpage.

An existing successful pair does **not** need to be redone after a normal code update.

## 5. Give visitors a listening link

The FPP settings page includes direct **Visitor player**, **Playback status**, and **QR image** links. For the default Device ID `fpp`:

- Listening page: `https://YOUR-HOST/listen/fpp/`
- Visitor QR image: `https://YOUR-HOST/api/shows/fpp/qr`

Place the QR on a sign with a brief instruction such as **Scan to listen to the lights**. On a phone, select **Listen live**; browsers typically require a deliberate tap before sound can start. The page deliberately does not display the internal device ID.

## 6. Test the complete system

1. Confirm the cPanel backend responds at `/health`.
2. On the Raspberry Pi, run `sudo systemctl status fpp-audio-preprocessed.service --no-pager` and confirm it is active.
3. Play a short MP3 through FPP and open `https://YOUR-HOST/api/shows/fpp` (replace `fpp` with your Device ID).
4. Expect `active: true` and `media_ready: true` while the show plays. The `position` should advance.
5. Open `/listen/fpp/` on a phone **with Wi-Fi turned off** and tap **Listen live**.
6. Verify audio, pause/resume, song transitions, QR navigation, and expected delay relative to your lights.

The streaming server stores and delivers copies of the audio files. It does **not** sample live audio output from the FPP controller. Use MP3 for the broadest phone compatibility.

## 7. Optional developer support

The player includes a small, **optional** panel for donations to the **software developer**, not the individual light-display owner. Listening is always free. The Stripe Buy Button loads only after a visitor opens the support panel.

To disable the panel, set `FPP_DEVELOPER_SUPPORT_ENABLED=0` in cPanel and restart the Python app. To change the Stripe recipient, update the `FPP_DEVELOPER_SUPPORT_URL`, `FPP_DEVELOPER_SUPPORT_BUTTON_ID`, and `FPP_DEVELOPER_SUPPORT_PUBLISHABLE_KEY` values together. Never put a Stripe *secret* API key in the page or the repository.

## 8. Troubleshooting

| Symptom | Likely explanation / first check |
|---|---|
| `/health` does not work | Passenger app not running; check cPanel application logs and Python environment |
| Pairing fails | HTTPS URL, pairing code, reverse-proxy HTTPS handling, or server connectivity |
| `active: false` | FPP not playing, status updates stopped, or network interruption |
| `active: true`, `media_ready: false` | File not uploaded; check music location, file permissions, cPanel PUT limits, storage permissions, or encoded filenames |
| A file on the server has `%20` in its name | Use the current backend, which decodes one extra layer of URL encoding. Rename old already-encoded files if needed |
| Listener page returns 404 | Check `~/web-player/index.html` relative to the application folder |
| Player appears unstyled | Check `styles.css` and `player.js`, then refresh browser cache |
| Player says preparing audio | Wait for upload; inspect agent and server logs if it persists |
| Phone does not play | Tap **Listen live** again, check MP3 codec, browser volume and media-ready state |
| Stripe button unavailable | Embedded checkout may be blocked; direct HTTPS support link remains usable |

Useful FPP commands:

```bash
sudo systemctl status fpp-audio-preprocessed.service --no-pager
sudo journalctl -u fpp-audio-preprocessed.service -n 50 --no-pager
tail -n 50 /home/fpp/media/logs/fpp-audio-preprocessed.log
```

Do not share your `FPP_STREAM_TOKEN`, pairing code, or private media directory contents when posting diagnostic logs.

## 9. Updates and backups

Back up the cPanel code, `private-media/`, the SQLite state, FPP configuration, and your environment-variable settings. Update backend code and web-player assets, **restart the Python application**, then update the FPP plugin through Plugin Manager. Keep the backend URL, token, Device ID, and pairing unchanged. Verify `/health`, `media_ready`, and phone playback before returning to a live show.

## 10. Privacy, security and media rights

The FPP agent uploads song files, filenames, playback timing and a device identifier to the HTTPS server designated by the show owner. Visitors receive those audio files from the server. Public audio streaming of copyrighted music may require permission even for a free holiday display. Review music distribution rights and your hosting provider’s terms before offering Internet-accessible listening.

The optional Stripe support panel may communicate with Stripe when opened; payments are processed by Stripe rather than the plugin. Contributions support the software developer and are not represented as tax-deductible charitable gifts. Do not expose private keys, credentials, or the `private-media/` directory on a public website.
