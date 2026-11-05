# Changelog

## v1.0.0-rc1 — November 2026

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
