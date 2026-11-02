#!/bin/bash
set -euo pipefail
if command -v systemctl >/dev/null; then
 sudo systemctl disable --now fpp-audio-preprocessed.service || true
 sudo rm -f /etc/systemd/system/fpp-audio-preprocessed.service
 sudo systemctl daemon-reload
fi
# Deliberately preserve settings and logs.
