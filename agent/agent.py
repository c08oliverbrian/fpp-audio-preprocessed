#!/usr/bin/env python3
"""LightShow Web Stream best-effort FPP media synchronization agent.

Never controls FPP playback; all network failures are isolated from the show.
"""
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import pathlib
import signal
import time
import urllib.error
import urllib.parse
import urllib.request

CFG = pathlib.Path('/home/fpp/media/plugindata/fpp-audio-preprocessed/settings.json')
LOG = pathlib.Path('/home/fpp/media/logs/plugin-fpp-audio-preprocessed.log')
MUSIC = pathlib.Path('/home/fpp/media/music')
STOP = False


def request_json(url, method='GET', data=None, token=None, timeout=8):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def upload(base, device, song, path, token):
    length = path.stat().st_size
    if length == 0:
        raise ValueError('empty media file')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            digest.update(chunk)
    url = (base + '/api/devices/' + urllib.parse.quote(device, safe='') +
           '/media/' + urllib.parse.quote(song, safe=''))
    # File-like body plus Content-Length avoids reading large audio files into Pi RAM.
    with path.open('rb') as stream:
        req = urllib.request.Request(url, data=stream, method='PUT', headers={
            'Authorization': 'Bearer ' + token,
            'X-Content-SHA256': digest.hexdigest(),
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(length),
        })
        with urllib.request.urlopen(req, timeout=150) as response:
            result = json.loads(response.read().decode('utf-8'))
            if not result.get('ok'):
                raise ValueError('backend rejected media upload')
    logging.info('Media uploaded: %r (%d bytes)', song, length)


def setup_log():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def main():
    global STOP
    setup_log()
    signal.signal(signal.SIGTERM, lambda *_: globals().update(STOP=True))
    signal.signal(signal.SIGINT, lambda *_: globals().update(STOP=True))
    logging.info('LightShow Web Stream FPP agent starting')
    previous = None
    uploaded = set()
    last_heartbeat = 0.0
    missing_logged = set()
    last_backend = None
    while not STOP:
        try:
            cfg = json.loads(CFG.read_text(encoding='utf-8')) if CFG.exists() else {}
            if not cfg.get('enabled') or not cfg.get('server_url') or not cfg.get('token'):
                time.sleep(5)
                continue
            base = str(cfg['server_url']).rstrip('/')
            token = cfg['token']
            device = cfg.get('device_id') or 'fpp'
            if base != last_backend:
                uploaded.clear()
                last_backend = base
                logging.info('Backend configured: %s', base)
            status = request_json('http://127.0.0.1/api/fppd/status')
            song = (status.get('current_song') or status.get('currentSong') or
                    status.get('media_filename') or status.get('mediaFilename') or '')
            if isinstance(song, dict):
                song = song.get('filename', '')
            song = pathlib.Path(str(song)).name
            state = str(status.get('status_name') or status.get('status') or 'unknown')
            elapsed = status.get('seconds_played', status.get('secondsPlayed', status.get('elapsed', 0)))
            try:
                elapsed = max(0.0, float(elapsed))
            except (TypeError, ValueError):
                elapsed = 0.0
            media = MUSIC / song if song else None
            signature = None
            if media and media.is_file():
                stat = media.stat()
                signature = (song, stat.st_size, stat.st_mtime_ns)
                if signature not in uploaded:
                    upload(base, device, song, media, token)
                    uploaded.add(signature)
                missing_logged.discard(song)
            elif song and song not in missing_logged:
                logging.warning('Media not found at expected path: %s', media)
                missing_logged.add(song)
            key = (song, state)
            if key != previous or time.monotonic() - last_heartbeat >= 1.0:
                data = {
                    'media': song, 'state': state, 'position': elapsed,
                    'display_name': cfg.get('display_name') or 'Your light show, live.',
                }
                response = request_json(
                    base + '/api/devices/' + urllib.parse.quote(device, safe='') + '/state',
                    method='POST', data=json.dumps(data).encode('utf-8'), token=token,
                )
                # New backend versions acknowledge media presence, allowing automatic recovery
                # if hosted storage is cleared or Passenger is moved to another volume.
                if signature and response.get('media_ready') is False:
                    uploaded.discard(signature)
                    logging.warning('Backend does not have %r; retrying upload', song)
                previous = key
                last_heartbeat = time.monotonic()
        except urllib.error.HTTPError as exc:
            logging.warning('Backend returned HTTP %d (%s)', exc.code, exc.reason)
        except urllib.error.URLError as exc:
            logging.warning('Network error: %s', exc.reason)
        except Exception as exc:
            logging.warning('Synchronization error: %s: %s', type(exc).__name__, exc)
        time.sleep(.5)
    logging.info('LightShow Web Stream agent stopped')


if __name__ == '__main__':
    main()
