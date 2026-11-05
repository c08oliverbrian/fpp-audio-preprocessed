"""LightShow Web Stream cPanel/Passenger backend (v1.0.0-rc2)."""
import os, re, json, time, uuid, hmac, hashlib, sqlite3, io, secrets
from pathlib import Path
from urllib.parse import unquote
from flask import Flask, request, jsonify, send_file, send_from_directory, abort, Response, redirect, url_for

BASE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('FPP_STREAM_MEDIA',str(BASE/'private-media'))).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
DB=ROOT/'state.sqlite3'
WEB=next((p for p in (BASE.parent/'web-player', BASE/'web-player') if (p/'index.html').is_file()), BASE.parent/'web-player')
TOKEN=os.environ.get('FPP_STREAM_TOKEN','')
PAIR=os.environ.get('FPP_PAIR_CODE','')
PUBLIC=os.environ.get('FPP_PUBLIC_URL','').rstrip('/')
MAX_BYTES=int(os.environ.get('FPP_MAX_MEDIA_BYTES',str(100*1024*1024)))
STALE=float(os.environ.get('FPP_STALE_SECONDS','12'))
# Developer-support configuration: the visitor can opt in, and show owners may turn it off.
SUPPORT_ENABLED=os.environ.get('FPP_DEVELOPER_SUPPORT_ENABLED','1').strip().lower() not in ('0','false','no','off')
SUPPORT_URL=os.environ.get('FPP_DEVELOPER_SUPPORT_URL','https://donate.stripe.com/6oUbJ2dYq8ZY7QB8at3sI00').strip()
SUPPORT_BUTTON=os.environ.get('FPP_DEVELOPER_SUPPORT_BUTTON_ID','buy_btn_1UYUWVJ4oxFRjDbmkMWeP15F')
SUPPORT_PUBLISHABLE=os.environ.get('FPP_DEVELOPER_SUPPORT_PUBLISHABLE_KEY','pk_live_51TADx9J4oxFRjDbmT3rEILfvDN6teHJcuFrbvKPIoC9xFmVwLB2UWK9qneWauQIrTn1lmVmiMnm8edbXqCtMpPIx00SXust7vZ')
ID=re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=MAX_BYTES+4096

def db():
    con=sqlite3.connect(DB,timeout=15)
    con.execute('PRAGMA busy_timeout=15000')
    con.execute('CREATE TABLE IF NOT EXISTS state(device TEXT PRIMARY KEY, media TEXT, state TEXT, position REAL, received REAL, display TEXT, session TEXT)')
    return con

def good_device(d):
    if not ID.fullmatch(d):abort(404)

def good_name(n):
    if not n or n in ('.','..') or len(n)>240 or '/' in n or '\\' in n or Path(n).name!=n:abort(400)

def route_media_name(name):
    """Decode one extra layer of proxy URL escaping, then validate the filename.

    Some Passenger proxy setups can deliver a literal "%20" to Flask after
    routing, where it otherwise would receive a space.  The resulting filename
    must be checked for slash/backslash traversal after decoding.
    """
    decoded = unquote(name)
    good_name(decoded)
    return decoded

def auth():
    value=request.headers.get('Authorization','')
    if not TOKEN or not hmac.compare_digest(value,'Bearer '+TOKEN):abort(401)

def playing(s):return str(s).lower() in ('playing','play','1','running')

def state_for(device):
    with db() as con:row=con.execute('SELECT media,state,position,received,display,session FROM state WHERE device=?',(device,)).fetchone()
    if not row:return None
    media,status,pos,received,display,session=row
    age=max(0,time.time()-received)
    active=age<STALE and playing(status) and bool(media)
    return {'device':device,'display_name':display or 'Your light show, live.','media':media,'state':status if age<STALE else 'offline',
            'position':round(max(0,pos+(age if active else 0)),3),'session_id':session,'active':active,
            'media_ready':bool(media and (ROOT/device/media).is_file()),'received_at':received}

@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options']='nosniff'
    r.headers['Cache-Control']='no-store'
    r.headers['X-Frame-Options']='DENY'
    return r

@app.get('/health')
def health():return jsonify(ok=True,version='1.0.0-rc2-cpanel')

@app.get('/api/player-config')
def player_config():
    # Only public metadata; tokens, pairing code, filesystem paths and backend secrets are never served.
    enabled=SUPPORT_ENABLED and SUPPORT_URL.startswith(('https://donate.stripe.com/','https://buy.stripe.com/'))
    return jsonify(developer_support={
        'enabled': enabled,
        'payment_url': SUPPORT_URL if enabled else '',
        'buy_button_id': SUPPORT_BUTTON if enabled else '',
        'publishable_key': SUPPORT_PUBLISHABLE if enabled else ''
    })

@app.post('/api/pair')
def pair():
    if not request.is_secure and os.environ.get('FPP_ALLOW_HTTP_PAIR')!='1':abort(403)
    data=request.get_json(silent=True) or {}
    code=str(data.get('code',''))
    if not PAIR or not TOKEN or not hmac.compare_digest(code,PAIR):abort(403)
    return jsonify(ok=True,token=TOKEN)

@app.post('/api/devices/<device>/state')
def set_state(device):
    good_device(device);auth()
    if request.content_length is None or request.content_length>262144:abort(413)
    data=request.get_json(silent=True)
    if not isinstance(data,dict):abort(400)
    media=str(data.get('media') or '')
    if media:good_name(media)
    try:pos=max(0,float(data.get('position',0)))
    except (ValueError,TypeError):abort(400)
    if not 0<=pos<1e9:abort(400)
    status=str(data.get('state','unknown'))[:40]
    display=str(data.get('display_name') or 'Your light show, live.')[:100]
    with db() as con:
        old=con.execute('SELECT media,state,position,session FROM state WHERE device=?',(device,)).fetchone()
        restart=not old or old[0]!=media or (playing(status) and not playing(old[1])) or (playing(status) and pos+2<old[2])
        sid=str(uuid.uuid4()) if restart else old[3]
        con.execute('INSERT INTO state VALUES(?,?,?,?,?,?,?) ON CONFLICT(device) DO UPDATE SET media=excluded.media,state=excluded.state,position=excluded.position,received=excluded.received,display=excluded.display,session=excluded.session',
                    (device,media,status,pos,time.time(),display,sid))
    return jsonify(ok=True,session_id=sid,media_ready=bool(media and (ROOT/device/media).is_file()))

@app.put('/api/devices/<device>/media/<path:name>')
def put_media(device,name):
    good_device(device);name=route_media_name(name);auth()
    length=request.content_length
    if length is None or not 0<length<=MAX_BYTES:abort(413)
    folder=ROOT/device;folder.mkdir(parents=True,exist_ok=True)
    tmp=folder/(uuid.uuid4().hex+'.partial')
    digest=hashlib.sha256();count=0
    try:
        with tmp.open('wb') as f:
            while True:
                chunk=request.stream.read(65536)
                if not chunk:break
                count+=len(chunk)
                if count>MAX_BYTES:abort(413)
                digest.update(chunk);f.write(chunk)
        if count!=length or not hmac.compare_digest(digest.hexdigest(),request.headers.get('X-Content-SHA256','')):abort(400)
        tmp.replace(folder/name)
        app.logger.info('Stored audio upload device=%s filename=%r bytes=%d', device, name, count)
    finally:tmp.unlink(missing_ok=True)
    return jsonify(ok=True,sha256=digest.hexdigest())

@app.get('/api/shows/<device>')
def show(device):
    good_device(device);s=state_for(device)
    return jsonify(s) if s else (jsonify(error='unknown device'),404)

@app.get('/api/shows/<device>/audio/<path:name>')
def audio(device,name):
    good_device(device);name=route_media_name(name)
    s=state_for(device)
    if not s or s['media']!=name or not s['media_ready']:abort(404)
    return send_file(ROOT/device/name,conditional=True,as_attachment=False)

@app.get('/api/shows/<device>/qr')
def qr(device):
    good_device(device)
    try:import qrcode
    except ImportError:return jsonify(error='qrcode not installed'),501
    url=(PUBLIC or request.url_root.rstrip('/'))+'/listen/'+device
    buf=io.BytesIO();qrcode.make(url).save(buf,format='PNG');buf.seek(0)
    return send_file(buf,mimetype='image/png')

@app.get('/listen/<device>')
def listen(device):
    good_device(device)
    # Relative JS/CSS asset links require a trailing slash on the listener URL.
    return redirect(url_for('listen_with_slash', device=device), code=302)

@app.get('/listen/<device>/')
def listen_with_slash(device):
    good_device(device)
    return send_from_directory(WEB,'index.html')

@app.get('/listen/<device>/<path:asset>')
def asset(device,asset):
    good_device(device)
    if asset not in ('player.js','styles.css','donate-qr.png'):abort(404)
    return send_from_directory(WEB,asset)

@app.errorhandler(413)
def too_large(_):return jsonify(error='upload too large; check hosting limits'),413

# Passenger imports `application` from passenger_wsgi.py.
application=app
