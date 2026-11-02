<?php
// Prototype configuration page. Keep token out of rendered HTML after save.
$path='/home/fpp/media/config/fpp-audio-preprocessed.json';
$cfg=is_file($path)?json_decode(file_get_contents($path),true):[];
$message='';
if ($_SERVER['REQUEST_METHOD']==='POST') {
  $cfg['enabled']=isset($_POST['enabled']);
  $cfg['server_url']=rtrim(trim($_POST['server_url']??''),'/');
  $cfg['device_id']=preg_replace('/[^a-zA-Z0-9_-]/','',$_POST['device_id']??'fpp');
  $cfg['display_name']=trim($_POST['display_name']??'');
  if (!empty($_POST['token'])) $cfg['token']=$_POST['token'];
  if (!empty($_POST['pair_code']) && filter_var($cfg['server_url'], FILTER_VALIDATE_URL)) {
    $endpoint=$cfg['server_url'].'/api/pair';
    $ch=curl_init($endpoint);
    curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>json_encode(['code'=>trim($_POST['pair_code'])]),CURLOPT_HTTPHEADER=>['Content-Type: application/json'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>8]);
    $result=curl_exec($ch);$http=curl_getinfo($ch,CURLINFO_HTTP_CODE);curl_close($ch);
    $paired=json_decode($result?:'',true);
    if ($http===200 && !empty($paired['token'])) {$cfg['token']=$paired['token'];$message='Paired successfully';}
    else {$message='Pairing failed: check server URL, code and connectivity';}
  }
  if (!filter_var($cfg['server_url'],FILTER_VALIDATE_URL) || !in_array(parse_url($cfg['server_url'],PHP_URL_SCHEME),['http','https'])) $message='Invalid server URL';
  else if ($message==='') {$message='Saved';} if ($message==='Saved' || $message==='Paired successfully') {file_put_contents($path,json_encode($cfg,JSON_PRETTY_PRINT),LOCK_EX);chmod($path,0600);}
}
function esc($x){return htmlspecialchars((string)$x,ENT_QUOTES,'UTF-8');}
?>
<h2>Preprocessed Audio Sync (Experimental)</h2>
<p><?=esc($message)?></p>
<form method="post">
<label><input type="checkbox" name="enabled" <?=!empty($cfg['enabled'])?'checked':''?>> Enabled</label><br>
<label>Backend URL <input size="55" name="server_url" value="<?=esc($cfg['server_url']??'')?>" placeholder="https://stream.example.com"></label><br>
<label>Device ID <input name="device_id" value="<?=esc($cfg['device_id']??'fpp')?>"></label><br>
<label>Show display name <input name="display_name" value="<?=esc($cfg['display_name']??'')?>" placeholder="Family Christmas Lights"></label><br>
<label>Pairing code (from backend setup) <input type="password" name="pair_code" autocomplete="off" placeholder="Paste once to pair"></label><br>
<label>Device token (advanced/manual) <input type="password" name="token" value="" placeholder="Leave blank to retain token"></label><br>
<button type="submit">Save</button>
</form>
<p><strong>Quick setup:</strong> Run <code>backend/setup.sh</code> and <code>backend/install-service.sh</code> on your backend Linux host, then enter its HTTPS URL and the pairing code above. Do not expose pairing over untrusted HTTP.</p>
<p>Backend must be deployed separately. See README.md. Listener URL: <code><?=esc(rtrim($cfg['server_url']??'','/').'/listen/'.($cfg['device_id']??'fpp'))?></code>. Generate QR from backend at <code>/api/shows/DEVICE_ID/qr</code>.</p>
