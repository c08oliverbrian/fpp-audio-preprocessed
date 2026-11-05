# LightShow Web Stream — Self-Hosted Audio for FPP

**Release candidate v1.0.0-rc2** — free, self-hosted MP3 audio for people watching a Falcon Player light show. Visitors scan a QR code, open the listener page on their phone, and tap **Listen live**. The player seeks to the position reported by FPP and makes periodic drift corrections. This is **approximate synchronization**, not guaranteed sample-accurate synchronization.

This repository contains **two independently deployed components**:

- **FPP plugin** (repository root, `agent/`, `content.php`, `scripts/`) — installed via FPP 10's Plugin Manager. Runs a background agent that observes playback and uploads media to the operator's backend.
- **Backend and public listener** (`backend/` and `web-player/`) — hosted separately using a cPanel Python 3.10+ / Passenger application. The backend serves media files, playback state, listener UI, and visitor QR codes.

**Listening is always free.** A small, optional support panel allows visitors to contribute directly to the **software developer**, *not* the display owner. Stripe is loaded only after the visitor opens this panel. A show operator can disable it with `FPP_DEVELOPER_SUPPORT_ENABLED=0` on the server.

## Instructions manual

**[Open the complete LightShow Web Stream user manual](docs/USER-MANUAL.md)** — setup, pairing, QR signs, playback, donation options, troubleshooting, and upgrades. The same manual is linked directly from the plugin configuration page in FPP.

## Quick deployment

1. **Back up** the FPP plugin's configuration and your cPanel application before upgrading. Do not replace `.env` files, cPanel variables, or `private-media/`.
2. Upload the **contents** of `backend/` to the existing cPanel Python app root (e.g. `~/fpp-audio-backend/`). Upload the **contents** of `web-player/` to `~/web-player/` (sibling of `fpp-audio-backend`). See [cPanel deployment and upgrade guide](docs/CPANEL-DEPLOY.md).
3. Restart the Python application. Verify `/health` and `/api/player-config`.
4. Commit the **repository root** files to your GitHub `main` branch. In FPP 10.3, go to **Content Setup → Plugin Manager → Installed → Check for Updates / Update**. Existing pairing settings are retained.
5. In FPP, open **LightShow Web Stream**, confirm your backend HTTPS URL and saved device token. The visitor page is `https://YOUR-HOST/listen/fpp/` (substitute your Device ID).
6. Test music upload, listener playback, QR, and the optional donation panel with a phone on cellular data. See [test checklist](docs/RELEASE-TESTS.md).

### Folder layout

```text
GitHub repository (FPP install root)
  pluginInfo.json
  content.php
  content_menu.inc
  agent/agent.py
  scripts/fpp_install.sh ...
  backend/cpanel_app.py, passenger_wsgi.py, requirements-cpanel.txt ...
  web-player/index.html, player.js, styles.css, donate-qr.png
  docs/

cPanel home
  fpp-audio-backend/     <-- contents of backend/
    cpanel_app.py
    passenger_wsgi.py
    private-media/       <-- keep this; existing uploads + state database
  web-player/            <-- contents of web-player/
    index.html
    player.js
    styles.css
    donate-qr.png
```

### Requirements and limitations

- FPP 10.x on Raspberry Pi/Linux with network access and service support. The released metadata lists FPP 10; other versions are untested.
- A separate, Internet-accessible **HTTPS** cPanel Python 3.10+ backend with Flask 3 and permissions to accept PUT audio uploads. Passenger/WSGI does not require systemd on shared hosting.
- FPP's music files at `/home/fpp/media/music/`. MP3 is recommended for iOS and Android compatibility.
- Show audio is **not** captured live from the Pi's audio output. The original audio file is uploaded and served to phones. The mobile browser may require a tap to allow playback.
- No guarantee of timing accuracy on Bluetooth, weak cellular connections, or during network outages.
- The mobile player and audio files are intentionally **public** on the configured show URL. Ensure you have necessary permissions for public Internet streaming of your music.
- Shared-hosting upload, storage, concurrency, and bandwidth quotas vary by provider. Test before a high-attendance show.

## Privacy and contributions

The Pi sends the chosen backend the audio filename, file content, playback position, show display name, and a device identifier. Backend operators control their server and retention. Visitors' browsers access that same host and the music files. When a visitor **opens** the support panel, the player may load Stripe's embedded Buy Button; alternatively, the visitor can open the direct donation page. Payment information is entered on Stripe, not on this server. The support link benefits the **software developer**, not the homeowner or any nonprofit.

To remove the support panel from your own deployment, set `FPP_DEVELOPER_SUPPORT_ENABLED=0` in cPanel and restart the Python application. To use a different recipient, configure the `FPP_DEVELOPER_SUPPORT_*` variables as explained in the deployment guide. The Stripe key included here is a **publishable** key, not a payment secret; never commit an `sk_live` value.

## Diagnostics

```bash
sudo systemctl status fpp-audio-preprocessed.service --no-pager
sudo journalctl -u fpp-audio-preprocessed.service -n 40 --no-pager
tail -n 40 /home/fpp/media/logs/fpp-audio-preprocessed.log
```

Test endpoints:

- `/health` – backend healthy
- `/api/shows/DEVICE_ID` – current position and `media_ready`
- `/listen/DEVICE_ID/` – visitor page
- `/api/shows/DEVICE_ID/qr` – visitor QR (not the separate developer-donation QR)
- `/api/player-config` – public player options only; no shared token

**Security:** Keep the server's `FPP_STREAM_TOKEN` and `FPP_PAIR_CODE` private. Disable `FPP_PAIR_CODE` after pairing if you do not need to pair another device. Do not put `private-media/` under `public_html`.

## Plugin directory listing

This candidate is **not yet certified** for FPP's official plugin catalog. FPP requires an appropriate open-source license, a privacy disclosure, successful automated checks, and testing on current stable/nightly FPP. See [the listing checklist](docs/RELEASE-TESTS.md). The repo includes a proposed MIT license; confirm ownership and licensing before publication.

## License

MIT, see `LICENSE` (subject to rights in any third-party files you add). This project is independent of FPP and Stripe, and is not endorsed by either.
