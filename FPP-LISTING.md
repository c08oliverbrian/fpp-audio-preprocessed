# Preparing an official FPP Plugin Manager listing

Your plugin can be installed by developer-mode GitHub URL before it is listed. For catalog inclusion:

1. Publish all files in this repository at the GitHub `main` branch root. Keep actual `.env`, secrets, `private-media` and SQLite DB **off GitHub**.
2. Verify pluginInfo.json in the official FPP plugin preview and privacy builder:
   - https://falconchristmas.github.io/fpp-data/plugin_preview/?repo=c08oliverbrian/fpp-audio-preprocessed
   - https://falconchristmas.github.io/fpp-data/plugin_privacy_builder/?repo=c08oliverbrian/fpp-audio-preprocessed
3. Confirm LICENSE copyright ownership and maintainers. Run the full test checklist and verify latest stable and current nightly FPP.
4. Read official rules at https://github.com/FalconChristmas/fpp-data/blob/master/PLUGINS.md . Follow its "Submit a plugin" issue-template workflow.
5. Wait for automated plugin check and fix any Blocker / Best practice reports. Particular pending review: the current service installer uses `sudo` to install a systemd service; FPP's checker may require changes. The ZIP does **not** guarantee acceptance.

## Suggested catalog description

**LightShow Radio — Self-Hosted Audio**

Free FPP plugin that uploads the currently playing music and timing to a show operator's independently hosted HTTPS backend. Visitors scan a QR code and listen on iPhone/Android with approximate track synchronization. Requires a separate cPanel Python 3.10+ Passenger/Flask backend; no central paid service. Optional, clearly labeled Stripe contribution panel supports the software developer; show owners can disable it without affecting streaming. MP3 recommended; Internet distribution rights and bandwidth are the operator's responsibility.
