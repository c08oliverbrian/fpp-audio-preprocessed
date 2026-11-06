# FPP catalog review fixes — v1.0.0-rc3

This package addresses the ten checker findings. It is a proposed release candidate; re-run the official listing scan before declaring the review passed.

## Correctly publish executable hooks

GitHub browser uploads do not reliably retain Unix executable bits. After copying release contents into your **local git clone**, run:

```bash
git add -A
git update-index --add --chmod=+x fpp_install.sh fpp_uninstall.sh scripts/fpp_install.sh scripts/fpp_uninstall.sh scripts/fpp_upgrade.sh
git diff --cached --summary
git commit -m "Fix FPP catalog checks and preserve existing configuration"
git push origin main
```

`git diff --cached --summary` should report `mode change 100644 => 100755` for each script previously tracked without execute permission; new executable files show `create mode 100755`. If your repository still contains separate root-level scripts, replace them with the included wrappers.

Then comment `/recheck` on the existing FPP submission issue.

## Deployment and migration

The plugin settings move from the deprecated config path to `plugindata/fpp-audio-preprocessed/settings.json`. The install/upgrade hook automatically *copies* an existing settings file there, preserving your backend URL, Device ID and token. The old config file is deliberately not deleted automatically. After confirming all works, remove the old file from `/home/fpp/media/config/` so FPP crash bundles don't include it. Back it up securely if needed.

The service name remains `fpp-audio-preprocessed.service`, and uninstall disables and removes its unit. Existing media on the independently hosted cPanel backend is unaffected. Log path is now `/home/fpp/media/logs/plugin-fpp-audio-preprocessed.log`.

## Optional developer contributions

To avoid loading Stripe JavaScript under FPP's CSP, the visitor support panel simply links to the Stripe-hosted donation page. The QR code remains. Payment is entirely optional. The backend and FPP agent protocols did not change. The payment page is hosted outside FPP.

## Verification

On the Pi, verify the settings copy exists and the service is active:

```bash
sudo systemctl status fpp-audio-preprocessed --no-pager
sudo -u fpp test -r /home/fpp/media/plugindata/fpp-audio-preprocessed/settings.json && echo 'Config readable'
tail -n 30 /home/fpp/media/logs/plugin-fpp-audio-preprocessed.log
```

Test a track with spaces in its name and verify `media_ready: true` in the backend. Check the donation link on a phone.

### Safety

Never commit token/config files to Git. No cPanel restart is necessary if only the included player files are updated. The old cPanel backend code remains compatible.
