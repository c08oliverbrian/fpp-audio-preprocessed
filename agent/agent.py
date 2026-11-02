#!/usr/bin/env python3
"""Independent, best-effort FPP status and media sync agent."""
import hashlib,json,logging,os,pathlib,signal,time,urllib.request,urllib.error
CFG=pathlib.Path('/home/fpp/media/config/fpp-audio-preprocessed.json')
LOG=pathlib.Path('/home/fpp/media/logs/fpp-audio-preprocessed.log')
STOP=False

def request(url,method='GET',data=None,token=None):
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(url,data=data,headers=headers,method=method)
 with urllib.request.urlopen(req,timeout=8) as r:return json.loads(r.read().decode())

def main():
 global STOP
 LOG.parent.mkdir(parents=True,exist_ok=True)
 logging.basicConfig(filename=LOG,level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
 signal.signal(signal.SIGTERM,lambda *_:globals().update(STOP=True))
 previous=None;sent=set();last_heartbeat=0
 while not STOP:
  try:
   cfg=json.loads(CFG.read_text()) if CFG.exists() else {}
   if not cfg.get('enabled') or not cfg.get('server_url') or not cfg.get('token'):
    time.sleep(5);continue
   base=cfg['server_url'].rstrip('/');token=cfg['token'];device=cfg.get('device_id','fpp')
   status=request('http://127.0.0.1/api/fppd/status')
   # FPP status field names vary; preserve original status in message for diagnostics.
   song=status.get('current_song') or status.get('currentSong') or status.get('media_filename') or ''
   if isinstance(song,dict):song=song.get('filename','')
   if not song:
    song=status.get('mediaFilename') or ''
   song=pathlib.Path(str(song)).name
   state=str(status.get('status_name') or status.get('status') or 'unknown')
   elapsed=status.get('seconds_played',status.get('secondsPlayed',status.get('elapsed',0)))
   try:elapsed=float(elapsed)
   except (TypeError,ValueError):elapsed=0.0
   media=pathlib.Path('/home/fpp/media/music')/song
   if song and media.is_file() and (song,media.stat().st_size,media.stat().st_mtime_ns) not in sent:
    payload=media.read_bytes()
    digest=hashlib.sha256(payload).hexdigest()
    # Binary file upload: avoid JSON/base64 memory expansion.
    req=urllib.request.Request(base+'/api/devices/'+urllib.parse.quote(device)+'/media/'+urllib.parse.quote(song),data=payload,method='PUT',headers={'Authorization':'Bearer '+token,'X-Content-SHA256':digest,'Content-Type':'application/octet-stream'})
    with urllib.request.urlopen(req,timeout=120) as resp:resp.read()
    sent.add((song,media.stat().st_size,media.stat().st_mtime_ns))
   key=(song,state)
   if key!=previous or time.monotonic()-last_heartbeat>=1:
    request(base+'/api/devices/'+urllib.parse.quote(device)+'/state','POST',json.dumps({'media':song,'state':state,'position':elapsed,'observed_at':time.time(),'display_name':cfg.get('display_name',device),'raw_status':status}).encode(),token)
    previous=key;last_heartbeat=time.monotonic()
  except Exception as e:
   logging.warning('Synchronization error: %s',type(e).__name__)
  time.sleep(0.5)
if __name__=='__main__':
 import urllib.parse
 main()
