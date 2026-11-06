#!/bin/bash
# FPP invokes plugin hooks with elevated privileges.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR=/home/fpp/media/plugindata/fpp-audio-preprocessed
CFG="$DATA_DIR/settings.json"
LEGACY_CFG=/home/fpp/media/config/fpp-audio-preprocessed.json
SERVICE=/etc/systemd/system/fpp-audio-preprocessed.service
LOG=/home/fpp/media/logs/plugin-fpp-audio-preprocessed.log

# The plugin's token must not be included in FPP crash-report config bundles.
install -d -o fpp -g fpp -m 700 "$DATA_DIR"
install -d -o fpp -g fpp -m 755 /home/fpp/media/logs
if [ ! -f "$CFG" ]; then
  if [ -f "$LEGACY_CFG" ]; then
    # Copy rather than move: preserves a rollback path to the prior version.
    cp "$LEGACY_CFG" "$CFG"
  else
    printf '%s\n' '{"enabled":false,"server_url":"","device_id":"fpp","token":""}' > "$CFG"
  fi
fi
chown fpp:fpp "$CFG"
chmod 600 "$CFG"
if [ ! -e "$LOG" ]; then
  install -o fpp -g fpp -m 644 /dev/null "$LOG"
fi

if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
  tmp="$(mktemp)"
  trap 'rm -f "$tmp"' EXIT
  sed "s|__PLUGIN_DIR__|$HERE|g" "$HERE/scripts/fpp-audio-preprocessed.service.in" > "$tmp"
  install -m 644 "$tmp" "$SERVICE"
  systemctl daemon-reload
  systemctl enable fpp-audio-preprocessed.service
  systemctl restart fpp-audio-preprocessed.service
fi
