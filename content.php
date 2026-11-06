<?php
// LightShow Web Stream configuration — tokens are never rendered back into the page.
$path = '/home/fpp/media/plugindata/fpp-audio-preprocessed/settings.json';
$cfg = is_file($path) ? (json_decode((string)file_get_contents($path), true) ?: []) : [];
$message = '';
$error = false;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $next = $cfg;
    $next['enabled'] = isset($_POST['enabled']);
    $next['server_url'] = rtrim(trim((string)($_POST['server_url'] ?? '')), '/');
    $next['device_id'] = preg_replace('/[^a-zA-Z0-9_-]/', '', (string)($_POST['device_id'] ?? 'fpp'));
    $next['display_name'] = trim((string)($_POST['display_name'] ?? ''));
    $url = $next['server_url'];
    if (!$next['device_id'] || strlen($next['device_id']) > 64 || !filter_var($url, FILTER_VALIDATE_URL)
        || parse_url($url, PHP_URL_SCHEME) !== 'https') {
        $message = 'Use an HTTPS backend URL and a valid Device ID (letters, numbers, underscores, hyphens).';
        $error = true;
    } else {
        if (!empty($_POST['token'])) $next['token'] = trim((string)$_POST['token']);
        if (!empty($_POST['pair_code'])) {
            $ch = curl_init($url . '/api/pair');
            curl_setopt_array($ch, [
                CURLOPT_POST => true,
                CURLOPT_POSTFIELDS => json_encode(['code' => trim((string)$_POST['pair_code'])]),
                CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_CONNECTTIMEOUT => 5,
                CURLOPT_TIMEOUT => 12,
                CURLOPT_FOLLOWLOCATION => false,
            ]);
            $result = curl_exec($ch);
            $http = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            $paired = json_decode($result ?: '', true);
            if ($http === 200 && !empty($paired['token'])) {
                $next['token'] = $paired['token'];
                $message = 'Paired successfully.';
            } else {
                $message = 'Pairing failed. Verify HTTPS, your pairing code, and cPanel connectivity.';
                $error = true;
            }
        }
        if (!$error) {
            $written = @file_put_contents($path, json_encode($next, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), LOCK_EX);
            if ($written === false) {
                $message = 'Could not save settings. Check configuration file permissions.';
                $error = true;
            } else {
                @chmod($path, 0600);
                $cfg = $next;
                if (!$message) $message = 'Settings saved.';
            }
        }
    }
}
function lightshowEsc($v) { return htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8'); }
$base = rtrim((string)($cfg['server_url'] ?? ''), '/');
$device = (string)($cfg['device_id'] ?? 'fpp');
?>
<style>
  .lsr-settings{max-width:760px;margin:18px 0 36px;font-size:15px;line-height:1.5}
  .lsr-banner{background:#181c39;color:#f6f5ff;padding:22px 25px;border-radius:14px;margin-bottom:20px}
  .lsr-banner h2{color:white;margin:0 0 5px}.lsr-banner p{margin:0;color:#d3d4eb}
  .lsr-banner-row{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
  .lsr-manual-link{display:inline-flex;align-items:center;justify-content:center;gap:6px;color:#fff!important;border:1px solid #b2b5f1;background:#ffffff20;border-radius:9px;padding:10px 14px;font-weight:700;text-decoration:none!important}
  .lsr-manual-link:hover,.lsr-manual-link:focus-visible{background:#ffffff32;text-decoration:underline!important}
  .lsr-panel{padding:21px 24px;border:1px solid #d8dce9;border-radius:13px;background:var(--bs-body-bg,#fff);margin-bottom:16px}
  .lsr-settings .lsr-field{display:flex;flex-direction:column;gap:5px;margin:13px 0}.lsr-field input:not([type=checkbox]){width:100%;max-width:640px;padding:9px;border:1px solid #a3acc3;border-radius:6px}
  .lsr-settings .lsr-note{font-size:13px;color:var(--bs-secondary-color,#6e7589);margin:7px 0}
  .lsr-settings code{overflow-wrap:anywhere}.lsr-settings .lsr-flash{padding:13px 16px;border-radius:9px;margin:13px 0;background:#e8f5ed;color:#155b37}
  .lsr-settings .lsr-flash.bad{background:#ffe9e9;color:#7b1d1d}.lsr-settings .lsr-save{background:#5f54d9;color:white;border:0;border-radius:7px;padding:12px 25px;font-weight:750;cursor:pointer}
</style>
<div class="lsr-settings">
  <div class="lsr-banner"><div class="lsr-banner-row">
    <div><h2>LightShow Web Stream</h2><p>Self-hosted streaming audio for visitors to your FPP light show</p></div>
    <a class="lsr-manual-link" href="https://github.com/c08oliverbrian/fpp-audio-preprocessed/blob/main/docs/USER-MANUAL.md" target="_blank" rel="noopener noreferrer" aria-label="Open LightShow Web Stream instructions manual in a new tab">Instructions manual ↗</a>
  </div></div>
  <?php if ($message): ?><div role="status" class="lsr-flash<?= $error ? ' bad' : '' ?>"><?=lightshowEsc($message)?></div><?php endif; ?>
  <form method="post">
    <div class="lsr-panel">
      <h3>Connection</h3>
      <label><input type="checkbox" name="enabled" <?= !empty($cfg['enabled']) ? 'checked' : '' ?>> Enable audio synchronization agent</label>
      <div class="lsr-field"><label for="lsr-url">Backend HTTPS URL</label><input id="lsr-url" type="url" name="server_url" required value="<?=lightshowEsc($cfg['server_url'] ?? '')?>" placeholder="https://stream.example.com"></div>
      <div class="lsr-field"><label for="lsr-device">Device ID</label><input id="lsr-device" name="device_id" maxlength="64" pattern="[A-Za-z0-9_-]+" required value="<?=lightshowEsc($device)?>"></div>
      <div class="lsr-field"><label for="lsr-display">Display name shown to visitors</label><input id="lsr-display" name="display_name" maxlength="100" value="<?=lightshowEsc($cfg['display_name'] ?? '')?>" placeholder="Our Christmas Lights"></div>
    </div>
    <div class="lsr-panel"><h3>Secure pairing</h3>
      <p class="lsr-note">Enter the pairing code from cPanel once. The device token is stored on the Pi and never displayed here.</p>
      <div class="lsr-field"><label for="lsr-pair">Pairing code</label><input id="lsr-pair" type="password" name="pair_code" autocomplete="off" placeholder="Leave empty if already paired"></div>
      <details><summary>Advanced: enter token manually</summary><div class="lsr-field"><label for="lsr-token">Device token</label><input id="lsr-token" type="password" name="token" autocomplete="off" placeholder="Leave blank to preserve existing token"></div></details>
      <p class="lsr-note">Pairing status: <?=!empty($cfg['token'])?'Token saved on this Pi':'Not yet paired'?></p>
    </div>
    <button class="lsr-save" type="submit">Save settings</button>
  </form>
  <div class="lsr-panel" style="margin-top:18px"><h3>Show &amp; diagnostics</h3>
    <?php if ($base): ?>
      <p><strong>Visitor player:</strong> <a target="_blank" rel="noopener noreferrer" href="<?=lightshowEsc($base.'/listen/'.rawurlencode($device).'/')?>"><?=lightshowEsc($base.'/listen/'.$device.'/')?></a></p>
      <p><strong>Playback status:</strong> <a target="_blank" rel="noopener noreferrer" href="<?=lightshowEsc($base.'/api/shows/'.rawurlencode($device))?>">Open backend status</a></p>
      <p><strong>QR image:</strong> <a target="_blank" rel="noopener noreferrer" href="<?=lightshowEsc($base.'/api/shows/'.rawurlencode($device).'/qr')?>">Open visitor QR code</a></p>
    <?php else: ?><p>Save your backend URL to show these links.</p><?php endif; ?>
    <p class="lsr-note">Agent log: <code>/home/fpp/media/logs/plugin-fpp-audio-preprocessed.log</code></p>
    <p class="lsr-note">The optional developer-support panel is configured on your cPanel backend; it never restricts listening.</p>
  </div>
</div>
