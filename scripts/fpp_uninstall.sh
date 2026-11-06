#!/bin/bash
set -euo pipefail
SERVICE=/etc/systemd/system/fpp-audio-preprocessed.service
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
  systemctl disable --now fpp-audio-preprocessed.service || true
fi
rm -f "$SERVICE"
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
  systemctl daemon-reload
fi
# Leave /home/fpp/media/plugindata/fpp-audio-preprocessed/settings.json
# (which contains pairing credentials) and logs for manual removal.
