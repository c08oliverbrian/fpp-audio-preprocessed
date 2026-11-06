#!/bin/bash
# FPP invokes plugin hooks with elevated privileges.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR=/home/fpp/media/plugindata/fpp-audio-preprocessed
CFG="$DATA_DIR/settings.json"
LEGACY_CFG=/home/fpp/media/config/fpp-audio-preprocessed.json
SERVICE=/etc/systemd/system/fpp-audio-preprocessed.service
LOG=/home/fpp/media/logs/plugin-fpp-audio-preprocessed.log

# FPP web UI typically runs as www-data, while the agent runs as fpp.
# Give each exactly the access required: web UI can save settings, agent reads them.
WEB_GROUP=www-data
if ! getent group "$WEB_GROUP" >/dev/null; then
  echo "Warning: www-data group missing; using fpp group for plugin settings" >&2
  WEB_GROUP=fpp
fi
install -d -o fpp -g "$WEB_GROUP" -m 2770 "$DATA_DIR"
install -d -o fpp -g fpp -m 755 /home/fpp/media/logs
# On upgrades, rescue the token from the old config location if an earlier
# migration left a blank or unpaired settings.json. Never overwrite a paired
# new config with stale credentials. Keep the legacy original for rollback.
python3 - "$CFG" "$LEGACY_CFG" <<'PYMIGRATE'
import json, os, pathlib, sys, tempfile
new, old = map(pathlib.Path, sys.argv[1:])
def load(p):
    try:
        value=json.loads(p.read_text())
        return value if isinstance(value,dict) else {}
    except (OSError, ValueError):return {}
current=load(new)
legacy=load(old)
if not new.exists() or not current.get('token'):
    if legacy.get('token') and legacy.get('server_url'):
        # Only rescue a previously paired configuration. Keep explicitly
        # populated current values, taking missing essentials from legacy.
        # An unpaired new file is not authoritative; restore the last paired
        # settings wholesale, including the enabled switch and display name.
        current = dict(legacy)
    elif not current:
        current={'enabled':False,'server_url':'','device_id':'fpp','token':''}
    if current:
        fd, tmp=tempfile.mkstemp(prefix='.settings-',dir=str(new.parent))
        try:
            with os.fdopen(fd,'w') as f:
                json.dump(current,f,indent=2)
                f.write('\n')
            os.replace(tmp,new)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
PYMIGRATE
chown fpp:"$WEB_GROUP" "$CFG"
chmod 660 "$CFG"
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
