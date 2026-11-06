'use strict';
// LightShow Web Stream v1.0.0-rc2 — browser-side approximate synchronization.
(() => {
  const device = decodeURIComponent(location.pathname.split('/')[2] || '');
  const $ = id => document.getElementById(id);
  const audio = $('audio');
  const button = $('listen');
  let listening = false;
  let media = '';
  let session = '';
  let current = null;
  let busy = false;
  let correctionAt = 0;
  let pendingAutoplay = false;
  const displaySong = name => String(name || '').replace(/\.[A-Za-z0-9]{2,5}$/, '').replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().replace(/\b[a-z]/g, c => c.toUpperCase());
  // The device ID is an internal routing identifier, never a visitor-facing show title.
  // Existing installations may have saved display_name='fpp' from the older agent.
  const publicShowName = state => {
    const title = String(state?.display_name || '').trim();
    const ids = [state?.device, device].filter(Boolean).map(value => String(value).trim().toLowerCase());
    return title && !ids.includes(title.toLowerCase()) ? title : 'Your light show, live.';
  };
  const formatTime = secs => Number.isFinite(secs) ? `${Math.floor(secs / 60)}:${String(Math.floor(secs % 60)).padStart(2, '0')}` : '–:––';

  function hint(message) { $('hint').textContent = message; }
  function uiStatus(label, live) {
    $('status').textContent = label;
    $('dot').classList.toggle('live', !!live);
  }
  function buttonLabel(text, icon, pressed) {
    $('playLabel').textContent = text;
    $('playIcon').textContent = icon;
    button.setAttribute('aria-pressed', String(!!pressed));
    button.setAttribute('aria-label', pressed ? 'Pause listening' : 'Start listening');
  }
  function seekTo(position) {
    if (!Number.isFinite(position) || audio.readyState < 1 || !Number.isFinite(audio.duration)) return;
    const target = Math.min(Math.max(0, position), Math.max(0, audio.duration - .2));
    try { audio.currentTime = target; } catch (_) { /* metadata not seekable yet */ }
  }
  function timeUi() {
    $('elapsed').textContent = formatTime(audio.currentTime);
    $('duration').textContent = formatTime(audio.duration);
    const percent = Number.isFinite(audio.duration) && audio.duration > 0 ? Math.min(100, Math.max(0, 100 * audio.currentTime / audio.duration)) : 0;
    $('progress').style.width = `${percent}%`;
    $('track').setAttribute('aria-valuenow', String(Math.round(percent)));
  }
  async function playIfReady() {
    if (!listening || !current?.active || !current?.media_ready || !audio.src) return;
    try {
      await audio.play();
      pendingAutoplay = false;
      buttonLabel('Pause listening', 'Ⅱ', true);
      hint('Listening live. Enjoy the show!');
    } catch (_) {
      pendingAutoplay = true;
      buttonLabel('Tap to play audio', '▶', false);
      hint('Your browser needs another tap to enable audio.');
    }
  }
  function setNewTrack(state) {
    media = state.media;
    session = state.session_id;
    audio.pause();
    audio.src = `/api/shows/${encodeURIComponent(device)}/audio/${encodeURIComponent(media)}`;
    audio.preload = listening ? 'auto' : 'none';
    audio.load();
    buttonLabel(listening ? 'Connecting audio…' : 'Listen live', '▶', false);
  }
  async function poll() {
    if (busy || !device) return;
    busy = true;
    try {
      const response = await fetch(`/api/shows/${encodeURIComponent(device)}`, { cache: 'no-store' });
      if (!response.ok) throw new Error('Show unavailable');
      const state = await response.json();
      current = state;
      $('show').textContent = publicShowName(state);
      $('song').textContent = state.media ? displaySong(state.media) : 'Waiting for music…';
      const live = !!state.active && !!state.media_ready;
      uiStatus(live ? 'ON AIR' : state.active ? 'PREPARING AUDIO' : 'OFF AIR', live);
      $('connection').textContent = live ? 'Streaming from the live light show' : state.active ? 'Preparing the soundtrack…' : 'Show is offline or between songs';

      if (!live) {
        audio.pause();
        if (listening) { buttonLabel('Waiting for music…', '▶', false); hint('We’ll reconnect when audio is available.'); }
        else buttonLabel('Listen live', '▶', false);
        return;
      }
      const changed = state.media !== media || state.session_id !== session;
      if (changed) setNewTrack(state);
      if (!listening) return;
      if (audio.readyState >= 1) {
        if (changed || Math.abs(audio.currentTime - state.position) > 1.25 && Date.now() - correctionAt > 3000) {
          seekTo(state.position); correctionAt = Date.now();
        }
      }
      if (audio.paused && !pendingAutoplay) await playIfReady();
    } catch (_) {
      uiStatus('RECONNECTING', false);
      $('connection').textContent = 'Trying to reach the show server…';
      if (!current) $('song').textContent = 'Waiting for music…';
    } finally { busy = false; }
  }

  button.addEventListener('click', async () => {
    if (listening && !pendingAutoplay) {
      listening = false; audio.pause();
      buttonLabel('Listen live', '▶', false);
      hint('Listening paused. The light show continues.');
      return;
    }
    listening = true; pendingAutoplay = false;
    buttonLabel('Connecting audio…', '▶', false);
    if (current?.active && current?.media_ready) {
      if (audio.preload === 'none') { audio.preload = 'auto'; audio.load(); }
      // Keep audio.play() in the click gesture for mobile Safari.
      if (audio.readyState >= 1) seekTo(current.position);
      await playIfReady();
    } else {
      hint('Waiting for the show to start…');
      await poll();
    }
  });
  audio.addEventListener('loadedmetadata', () => {
    if (current?.active && current.media === media) seekTo(current.position);
    timeUi();
    if (listening && !pendingAutoplay) void playIfReady();
  });
  audio.addEventListener('timeupdate', timeUi);
  audio.addEventListener('durationchange', timeUi);
  audio.addEventListener('error', () => {
    buttonLabel('Retry audio', '▶', false);
    pendingAutoplay = true;
    hint('Audio cannot be loaded. Check the file format and try again.');
  });
  $('volume').addEventListener('input', event => {
    const value = Math.max(0, Math.min(100, Number(event.target.value)));
    audio.volume = value / 100;
    $('volvalue').textContent = `${value}%`;
  });

  // Developer contributions are completely optional and never block playback.
  // Stripe is contacted only after the visitor explicitly opens the support panel.
  let supportConfig = null;
  const defaultLink = 'https://donate.stripe.com/6oUbJ2dYq8ZY7QB8at3sI00';
  async function setupSupport() {
    try {
      const result = await fetch('/api/player-config', { cache: 'no-store' });
      if (!result.ok) return;
      const data = await result.json();
      if (!data?.developer_support?.enabled) return;
      supportConfig = data.developer_support;
      const link = supportConfig.payment_url;
      if (!/^https:\/\/(?:donate\.|buy\.)stripe\.com\//.test(link || '')) return;
      $('donateLink').href = link;
      $('donateQrWrap').hidden = link !== defaultLink;
      $('supportCard').hidden = false;
    } catch (_) { /* Never affect music playback if config is unavailable. */ }
  }
  $('supportToggle').addEventListener('click', () => {
    const opened = $('supportToggle').getAttribute('aria-expanded') === 'true';
    $('supportToggle').setAttribute('aria-expanded', String(!opened));
    $('supportBody').hidden = opened;

  });
  poll();
  void setupSupport();
  setInterval(poll, 1500);
})();
