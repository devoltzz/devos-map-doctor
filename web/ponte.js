// ponte.js - the bridge of the Doctor's page in the browser (1.6). The page (app.js, the same as the exe's) talks to
// `window.pywebview.api`; in the exe that is pywebview and a worker process per job, here it is two Web Workers with
// Pyodide (worker.js): `main` for the actions and `quiet` for the tabs that load in the background, so a Fix does not
// wait for the tabs. Nothing leaves the computer: the map is read by the worker from the file the user picked, and
// what the jobs write comes back as a download.
//
// window.DOCTOR_WEB (config.js, written by build_site.py): {version, repository, sizeLimit}.
// window.doctorWeb: what the site's own parts use (fila.js, the queue of several maps): jobs that do not show in the
// page, the files they wrote, the size limit.
'use strict';

(() => {
  const CONFIG = window.DOCTOR_WEB || {};
  const SETTINGS = 'doctor.settings';
  const SIZE_LIMIT = CONFIG.sizeLimit || 450 * 1024 * 1024;
  const workers = {};            // key -> {w, ready: Promise}
  const picked = new Map();      // the worker path of each file the user picked -> File
  const where = new Map();       // the worker path of each file a job wrote -> worker key
  const jobs = new Map();        // job id -> {key, outs, silent?: {resolve, progress}}
  let newVersion = false;        // a new version of the site took over (see the service worker below)
  const reads = new Map();       // read id -> {resolve, reject}
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

  // the end of a job: its files are fetched from the worker that wrote them; a file it saved where the page asked
  // (`pick_save`, `pick_folder`: under /out) is downloaded at once, as the exe would have written it there
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

  // a file picked with the browser's dialog, or dropped on the page: given to both workers under a worker path. A map
  // above the size limit is refused here (the browser would run out of memory half way): the Windows program does it
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
    // a job is stopped by ending its worker: the other jobs queued there end as cancelled too, and a new worker
    // starts with the picked files (what the old one wrote is gone, as the exe drops a cancelled job's output)
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
    // the exe offers the file name index when it is missing; here it is missing until the browser keeps it
    check_update: async () => {
      try {
        if (!('caches' in window) || await caches.match('names.npz')) return false;
        const r = await fetch('names.npz', { method: 'HEAD' });
        if (!r.ok) return false;
        emit({ type: 'index', release: { index_size: Number(r.headers.get('content-length')) || 0 }, missing: true });
      } catch (e) { /* offline or no index on this host */ }
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
    // a job that does not show in the page: -> Promise of its last event (result, error or cancelled)
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

  // a map dropped on the page: the exe's window sends its path in a `dropped` event; here the file itself is read
  document.addEventListener('drop', e => {
    const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f && /\.w3[xmn]$/i.test(f.name) && !tooBig(f)) emit({ type: 'dropped', path: addPicked(f, '/maps') });
  });

  // what is different in the browser: the About page, where the results go, and the browsers it is made for
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

  // 1.6.3: a new version takes over by itself. The service worker answers from its cache, so the page that opened came
  // from the old one; when the new worker (skipWaiting + clients.claim in sw.js) takes control, the page reloads to be
  // the new version too -- by itself only on the home screen with nothing running (what the user sees right after
  // opening the site); with a map open or a job running, a notice with a Reload button, so no result on screen is lost.
  // Not on the first visit: there the page is already the newest. `update()` checks for a new sw.js as the page opens.
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
