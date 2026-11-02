# FPP Audio Preprocessed v0.2 — experimental end-to-end listener

**What works in code:** FPP agent polls status and uploads referenced media, backend receives file and state, listener page plays uploaded audio via HTTP byte-range requests, seeks to reported position on joining, and periodically corrects large drift. QR PNG generation is supported with optional `qrcode` dependency. **Not hardware-tested, not precisely synchronized, not production-ready.**

## Backend installation

Python 3.9+; optionally `python3 -m pip install 'qrcode[pil]'` for QR images.

```bash
export FPP_STREAM_TOKEN='replace-with-a-long-random-secret'
export FPP_STREAM_MEDIA="$PWD/media"
export FPP_PUBLIC_URL='https://your-public-domain.example'
python3 backend/server.py
```

Backend listens on port 8088 by default. Deploy behind an HTTPS reverse proxy such as Caddy or nginx. Set FPP_PUBLIC_URL to the public HTTPS URL. **Do not expose this prototype to the public Internet without rate limits, access control and hardening.** Listener URLs are intentionally public and audio files are accessible to anyone knowing the device ID; use only media you have the right to stream. Browser support is best with MP3 or AAC; WAV may work, other file formats vary by browser. Preprocessing in this prototype means uploading original files, not transcoding.

## FPP installation

FPP Plugin Manager expects a Git URL rather than a local ZIP. Publish this plugin directory to your own GitHub repository and change `pluginInfo.json` `srcURL` and `homeURL` to that repository before installing. For manual testing copy directory to `/home/fpp/media/plugins/fpp-audio-preprocessed` and run `sudo bash scripts/fpp_install.sh` in that directory. This installs a systemd agent service. Configure backend URL, device ID, display name, token, and enabled state in plugin UI. The backend and FPP must share the same token. The FPP agent polls `/api/fppd/status`; FPP version-specific field names and plugin UI behavior require verification on real hardware.

## QR and listener

Listener: `https://your-public-domain.example/listen/fpp` (replace `fpp` with device ID).
QR PNG: `https://your-public-domain.example/api/shows/fpp/qr` (requires optional `qrcode` Python package).
Open listener on phone, tap **Listen**. It loads the current track and seeks to the reported show position. On a track transition it loads the new track. Sync polling is 1.5 seconds and correction threshold 1.25 seconds. The show must already be running and the file uploaded. No automatic phone autoplay before user gesture.

## API

- `GET /health`: server health
- `PUT /api/devices/{id}/media/{filename}`: authenticated raw media upload with SHA-256 header
- `POST /api/devices/{id}/state`: authenticated JSON playback state (`media`, `state`, `position`, `display_name`)
- `GET /api/shows/{id}`: public show state and interpolated position
- `GET /api/shows/{id}/audio/{filename}`: public current audio with HTTP Range support
- `GET /api/shows/{id}/qr`: public QR PNG (optional dependency)
- `GET /listen/{id}`: responsive browser player

## Limitations

- **No guaranteed sync:** browser decode/output latency, network jitter, FPP status position precision, and Bluetooth delays are not compensated. Drift correction is coarse.
- Status and session registry are in-memory, lost on backend restart. Media persists on disk.
- Public endpoints have no listener auth, throttling or bandwidth caps. Deploy only for controlled hobbyist testing until hardened.
- FPP audio status fields may differ between versions; verify on device. The current agent may not identify every FPP playlist format.
- Uploaded media is not transcoded; browser may not support some FPP audio formats.
- No automatic media-library-wide pre-upload; only active referenced files.
- Agent currently reads full media into RAM when uploading (up to available memory), which should be improved before large deployments.
- Multiple devices supported by device ID; each device must be uniquely named. Shared device bearer token in v0.2.

## Manual test

Start backend, post a short MP3 as an authorized upload and then post state with `media`, `state: playing`, `position: 30`. Open `/listen/{device}` and press Listen; verify it seeks near 30 seconds. Test new song, stop, disconnected server, iPhone Safari, Android Chrome, and network throttling. No real FPP hardware or mobile browser measurements have been performed in this environment.

## v0.3 simplified backend setup (Linux VPS or Raspberry Pi)

```bash
cd backend
./setup.sh             # creates a random shared token and pairing code; installs QR dependency
./install-service.sh   # starts backend now and on reboot using systemd
```

The backend listens on port 8088. Put it behind an HTTPS reverse proxy with a domain and valid certificate (required for public use). In the FPP plugin settings enter the HTTPS backend URL, the pairing code printed by setup, and click Save. FPP exchanges the pairing code for the token and saves it to the existing protected configuration file. You no longer need to copy the token manually. For local trusted-network testing only, an http://LAN-IP:8088 URL can be used. The pairing code remains reusable until rotated: treat it as a secret and never expose the backend publicly without HTTPS, rate limiting, and firewall protections. Pairing uses a single shared token across devices and is intended for controlled hobbyist use, not production Internet exposure.

Useful commands: `sudo systemctl status fpp-audio-backend`, `sudo journalctl -u fpp-audio-backend -f`, `sudo systemctl restart fpp-audio-backend`. To rotate credentials, stop service, edit `.env` and update FPP pairing.

The automated installer does not configure DNS, HTTPS certificates, router port forwarding, or cloud firewalls. It has not been hardware tested.
