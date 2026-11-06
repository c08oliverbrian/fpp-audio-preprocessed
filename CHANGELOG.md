## v1.0.0-rc3 — FPP listing compliance

- Executable install/uninstall hooks (both root and scripts paths), with Git mode instructions.
- Removed sudo from systemd installer and uninstall hooks.
- FPP-compliant plugin log path and private plugindata settings with safe migration.
- Declared Stripe payment destinations and the system service in privacy metadata.
- External Stripe payment page instead of CSP-blocked embedded script.
- Added gitHistory release notes and shortened privacy summary.

## 1.0.0-rc2 — LightShow Web Stream (user-interface refinement)

- Updated the visible product name to **LightShow Web Stream**; plugin and service identifiers remain unchanged to preserve upgrades and pairing.
- Added an **Instructions manual** link prominently in the FPP plugin settings page, pointing to the new comprehensive `docs/USER-MANUAL.md` in GitHub.
- Removed the large decorative square artwork and the redundant hero subtitle from the mobile player.
- Prevented the internal Device ID (e.g. `fpp`) from appearing as the public show title, including with previously saved configurations.
- Retained existing streaming API, Stripe donation, cPanel storage and auth behavior.

# Changelog

## v1.0.0-rc2 — November 2026

- New responsive dark-themed listener player with accessible listening controls, live status, playback progress, and volume.
- Optional **Support the software developer** panel; clearly distinguishes contributions from light-show donations.
- Integrated user-supplied live Stripe Buy Button, lazily loaded after the listener expands the panel.
- Included user-provided, verified Stripe donation QR and direct Stripe payment link as a fallback.
- cPanel `FPP_DEVELOPER_SUPPORT_ENABLED=0` disables developer contributions without changing the plugin or visitor audio flow.
- Retained v0.4.1 Passenger filename decoding fix for spaces encoded as `%20`, and trailing-slash listener asset routing.
- Agent logs media uploads, missing files, HTTP failures, and restarts. Best-effort recovery if the backend reports missing media.
- Refined FPP configuration page, persistent pairing, and links to visitor/status/QR endpoints.
- Added FPP 10-compatible metadata, a plugin icon, menu entry, privacy disclosure, MIT license proposal, deployment docs and test checklist.

### Known limits

- Approximate synchronization only; not sample accurate and not designed to compensate for Bluetooth/cellular playback latency.
- Requires a separate Internet-accessible backend that supports audio-sized PUT requests; not tested for high concurrency.
- Real cPanel + FPP integration, mobile audio, and Stripe transaction processing must be verified on the intended deployment before public launch.
- Official FPP listing and installer automated checks are pending.
