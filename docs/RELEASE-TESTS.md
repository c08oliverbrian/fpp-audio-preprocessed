# Release-candidate test and FPP listing checklist

## Local sanity tests (provided in `tests/`)

- `python3 -m compileall -q agent backend` — Python compiles.
- `php -l content.php` — FPP settings page parses.
- `node --check web-player/player.js` — browser JS syntax.
- `python3 -m unittest discover -s tests -v` — metadata, filenames, asset paths and privacy checks.

## Manual integration (still required before a full production release)

- [ ] Upgrade an already-paired Pi running FPP 10.3: server URL, token, and saved Device ID survive a GitHub plugin update and reboot.
- [ ] Start, pause, resume, change tracks, stop, and wait for stale-state timeout. Show playback must continue if backend is offline.
- [ ] Upload MP3s with spaces, punctuation and mixed case. Test a 3 MB track and a larger track within the host's limits.
- [ ] Verify browser player on iPhone Safari and Android Chrome over cellular, including late join, track transition, foreground/background/resume, poor connectivity.
- [ ] Check `/listen/DEVICE/`, JS/CSS, QR, HTTP Range responses, and no secret token in the `/api/player-config` response.
- [ ] Check donation panel can be opened and closed; no Stripe script is loaded inside the player. Verify the developer link and supplied QR always appear; donations remain voluntary.
- [ ] Verify upload logs, log rotation, and graceful service shutdown; review cPanel Passenger logs.
- [ ] Check multiple visitors and peak bandwidth on the intended shared hosting plan.
- [ ] Verify music usage rights and a suitable privacy statement for the actual operator.

## FPP catalog submission (not yet completed)

- [ ] Review the proposed MIT license and rights ownership.
- [ ] Check plugin icon, author attribution, `pluginInfo.json` version ranges and `privacy` disclosure against the current FPP Template metadata guide and privacy builder.
- [ ] Test with latest released FPP **and** a current nightly build.
- [ ] Run FPP automated plugin check and resolve all Blocker/Best practice notices (especially service installation and use of `sudo`).
- [ ] Submit to the FPP `fpp-data` repository following its `PLUGINS.md` process and await maintainer review.

The plugin is not listed or approved merely by publishing to GitHub. The supplied ZIP is an **RC**, not a claim of FPP certification or commercial readiness.
