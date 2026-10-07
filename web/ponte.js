// The bridge between the page and the site's Web Workers (window.pywebview.api).
'use strict';

(() => {
  const CONFIG = window.DOCTOR_WEB || {};
  const SETTINGS = 'doctor.settings';
  const SIZE_LIMIT = CONFIG.sizeLimit || 450 * 1024 * 1024;
  const workers = {};
  const picked = new Map();
  const where = new Map();
  const jobs = new Map();
  let newVersion = false;
  const reads = new Map();
  let next = 0;

  const emit = ev => window.doctor && window.doctor.onEvent(ev);
  const say = (text, opts) => (typeof window.toast === 'function' ? window.toast(text, opts) : window.alert(text));
  const mb = n => Math.round(n / 1048576) + ' MB';

  function spawn(key) {
    const w = new Worker('worker.js', { type: 'module' });
    let ok, bad;
    const rec = { w, ready: new Promise((a, b) => { ok = a; bad = b; }) };
    rec.ready.catch(() => {});
    w.onmessage = ev => {
      const m = ev.data;
      if (m.type === 'ready') ok();
      else if (m.type === 'boot_failed') bad(new Error(m.message));
      else if (m.type === 'read') {
        const r = reads.get(m.rid);
        reads.delete(m.rid);
        if (r) m.error ? r.reject(new Error(m.error)) : r.resolve(m);
      } else if (m.type === 'event') {
        const e = JSON.parse(m.event);
        if (e.type === 'output' || (/^index_/.test(e.type) && key !== 'main')) return;
        const job = jobs.get(e.job);
        if (job && job.silent) {
          if (e.type === 'progress') { if (job.silent.progress) job.silent.progress(e.label); return; }
          finish(key, e);
          job.silent.resolve(e);
          return;
        }
        if (e.type === 'result' || e.type === 'error') finish(key, e);
        emit(e);
      }
    };
    w.onerror = ev => bad(new Error(ev.message || 'the worker could not start'));
    workers[key] = rec;
    for (const [path, file] of picked) w.postMessage({ type: 'file', path, file });
    return rec;
  }

  function worker(key) { return workers[key] || spawn(key); }

  function finish(key, e) {
    const job = jobs.get(e.job);
    jobs.delete(e.job);
    for (const p of e.written || []) where.set(p, key);
    if (job && !job.silent && e.type === 'result') {
      for (const p of job.outs) if (where.has(p) || isOutFolder(p)) download(p);
    }
  }

  function isOutFolder(p) { return [...where.keys()].some(k => k.startsWith(p.replace(/\/?$/, '/'))); }

  function request(key, msg) {
    const rid = 'r' + (++next);
    return new Promise((resolve, reject) => {
      reads.set(rid, { resolve, reject });
      worker(key).w.postMessage(Object.assign({ rid }, msg));
    });
  }

  function fetchFile(path) {
    let key = where.get(path);
    if (!key) for (const [p, k] of where) if (p.startsWith(path.replace(/\/?$/, '/'))) { key = k; break; }
    return request(key || 'main', { type: 'read', path });
  }

  function saveBytes(bytes, name) {
    const url = URL.createObjectURL(new Blob([bytes]));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  async function download(path) {
    const r = await fetchFile(path);
    saveBytes(r.bytes, r.name);
  }

  function tooBig(file) {
    if (file.size <= SIZE_LIMIT) return false;
    say(file.name + ' is ' + mb(file.size) + ': maps above ' + mb(SIZE_LIMIT) + ' need more memory than a browser ' +
      'gives a page. Use the Windows program (Download on GitHub).', { bad: true, sticky: true,
      actions: CONFIG.repository ? [['Open GitHub', () => window.open('https://github.com/' + CONFIG.repository +
        '/releases/latest', '_blank', 'noopener')]] : [] });
    return true;
  }

  function addPicked(file, dir) {
    const path = dir + '/' + file.name;
    picked.set(path, file);
    for (const rec of Object.values(workers)) rec.w.postMessage({ type: 'file', path, file });
    return path;
  }

  function choose(accept, dir, isMap) {
    return new Promise(resolve => {
      const input = document.createElement('input');
      input.type = 'file';
      if (accept) input.accept = accept;
      input.onchange = () => {
        const f = input.files[0];
        resolve(f && !(isMap && tooBig(f)) ? addPicked(f, dir) : null);
      };
      input.addEventListener('cancel', () => resolve(null));
      input.click();
    });
  }

  const ACCEPT = { map: '.w3x,.w3m,.w3n', translation: '.json,.html,.htm', package: '.mix,.asi,.dll,.mpq',
    image: '.png,.jpg,.jpeg,.bmp,.tga,.blp' };

  function loadSettings() {
    try { return JSON.parse(localStorage.getItem(SETTINGS) || '{}'); } catch (e) { return {}; }
  }

  function startJob(task, params, silent) {
    const id = 'job' + (++next);
    const key = params && params.quiet ? 'quiet' : 'main';
    const job = Object.assign({}, params || {}, { task, id });
    delete job.quiet;
    const outs = [job.file, job.folder].filter(p => typeof p === 'string' && p.startsWith('/out/'));
    jobs.set(id, { key, outs, silent });
    const rec = worker(key);
    rec.ready.catch(e => {
      if (!jobs.has(id)) return;
      const ev = { type: 'error', job: id, message: 'The engine could not start in this browser: ' + e.message };
      jobs.delete(id);
      if (silent) silent.resolve(ev); else emit(ev);
    });
    rec.w.postMessage({ type: 'job', job });
    return id;
  }

  const api = {
    hello: async () => Object.assign({ version: CONFIG.version || '?', app: "Devo's Map Doctor", map: null,
      repository: CONFIG.repository || null, web: true }, { settings: Object.assign(loadSettings(), { recent: [] }) }),
    save_settings: async data => {
      try { localStorage.setItem(SETTINGS, JSON.stringify(Object.assign({}, data, { recent: [] }))); } catch (e) { }
      return true;
    },
    pick_map: () => choose(ACCEPT.map, '/maps', true),
    pick_file: kind => choose(ACCEPT[kind], kind === 'map' ? '/maps' : '/in', kind === 'map'),
    pick_save: async suggested => '/out/' + (suggested || 'file'),
    pick_folder: async () => '/out/extracted' + (++next),
    read_file: async path => {
      const f = picked.get(path);
      if (!f) return null;
      const b = new Uint8Array(await f.arrayBuffer());
      let s = '';
      for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
      return btoa(s);
    },
    write_text: async (path, text) => {
      saveBytes(new TextEncoder().encode(text), path.split('/').pop());
      return true;
    },
    open_folder: async path => { if (!path) return false; await download(path); return true; },
    open_url: async url => { if (/^https:\/\//.test(url)) window.open(url, '_blank', 'noopener'); return true; },
    report_problem: async (title, body) => {
      if (!CONFIG.repository) return false;
      const q = new URLSearchParams({ title: title.slice(0, 200), body: body.slice(0, 6000) });
      window.open('https://github.com/' + CONFIG.repository + '/issues/new?' + q, '_blank', 'noopener');
      return true;
    },
    start: async (task, params) => startJob(task, params, null),
    cancel: async id => {
      const job = jobs.get(id);
      if (!job) return false;
      const rec = workers[job.key];
      delete workers[job.key];
      rec.w.terminate();
      for (const [j, x] of [...jobs]) {
        if (x.key !== job.key) continue;
        jobs.delete(j);
        if (x.silent) x.silent.resolve({ type: 'cancelled', job: j }); else emit({ type: 'cancelled', job: j });
      }
      for (const [p, k] of [...where]) if (k === job.key) where.delete(p);
      return true;
    },
    busy: async () => jobs.size > 0,
    check_update: async () => {
      try {
        if (!('caches' in window) || await caches.match('names.npz')) return false;
        const r = await fetch('names.npz', { method: 'HEAD' });
        if (!r.ok) return false;
        emit({ type: 'index', release: { index_size: Number(r.headers.get('content-length')) || 0 }, missing: true });
      } catch (e) { }
      return true;
    },
    install_update: async () => false,
    download_index: async () => {
      for (const rec of [worker('main'), worker('quiet')]) rec.w.postMessage({ type: 'index', url: 'names.npz' });
      return true;
    },
  };

  window.pywebview = { api };

  window.doctorWeb = {
    sizeLimit: SIZE_LIMIT,
    tooBig,
    addPicked,
    run: (task, params, progress) => new Promise(resolve => startJob(task, params, { resolve, progress })),
    cancelAll: async () => { for (const id of [...jobs.keys()]) if (jobs.get(id).silent) await api.cancel(id); },
    read: path => fetchFile(path),
    remove: path => {
      const key = where.get(path) || 'main';
      where.delete(path);
      return request(key, { type: 'delete', path });
    },
    zip: (paths, name) => request('main', { type: 'zip', paths, name }),
    saveBytes,
  };

  document.addEventListener('drop', e => {
    const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f && /\.w3[xmn]$/i.test(f.name) && !tooBig(f)) emit({ type: 'dropped', path: addPicked(f, '/maps') });
  });

  function adapt() {
    const report = document.getElementById('btnReport');
    if (report && !document.getElementById('btnAbout')) {
      const about = document.createElement('a');
      about.className = 'btn ghost';
      about.id = 'btnAbout';
      about.href = 'about.html';
      about.textContent = 'About';
      report.parentNode.insertBefore(about, report);
    }
    for (const p of document.querySelectorAll('#welcome .drop p.faint')) {
      if (/next to it/.test(p.textContent)) {
        p.textContent = 'Your map never leaves your computer and is never changed: results come back as downloads.';
      }
    }
    const ua = navigator.userAgent;
    const mobile = /Android|iPhone|iPad|iPod|Mobile/i.test(ua) ||
      (navigator.maxTouchPoints > 1 && /Macintosh/.test(ua));
    const safari = /Safari/.test(ua) && !/Chrome|Chromium|Edg|Firefox|FxiOS|CriOS/.test(ua);
    if (mobile || safari) {
      setTimeout(() => say('Made for Chrome, Edge and Firefox on a computer: here the Doctor may be slow or stop ' +
        'on big maps.', { sticky: true }), 500);
    }
  }

  if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
    const hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (!hadController || newVersion) return;
      newVersion = true;
      const home = document.getElementById('welcome');
      if (!jobs.size && (!home || !home.classList.contains('hidden'))) {
        location.reload();
        return;
      }
      say('A new version of the Doctor is ready: reload the page to use it.',
        { sticky: true, actions: [['Reload', () => location.reload()]] });
    });
    navigator.serviceWorker.register('sw.js').then(r => r.update()).catch(() => null);
  }
  worker('main');
  window.addEventListener('DOMContentLoaded', () => {
    adapt();
    window.dispatchEvent(new Event('pywebviewready'));
  });
})();
