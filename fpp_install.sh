#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p /home/fpp/media/config /home/fpp/media/logs
if [ ! -f /home/fpp/media/config/fpp-audio-preprocessed.json ]; then
  printf '%s\n' '{"enabled":false,"server_url":"","device_id":"fpp","token":""}' > /home/fpp/media/config/fpp-audio-preprocessed.json
  chmod 600 /home/fpp/media/config/fpp-audio-preprocessed.json
fi
if command -v systemctl >/dev/null; then
  sed "s|__PLUGIN_DIR__|$HERE|g" "$HERE/scripts/fpp-audio-preprocessed.service.in" > /tmp/fpp-audio-preprocessed.service
  sudo install -m 644 /tmp/fpp-audio-preprocessed.service /etc/systemd/system/fpp-audio-preprocessed.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now fpp-audio-preprocessed.service
fi
