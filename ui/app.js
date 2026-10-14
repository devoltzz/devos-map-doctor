// The page: the modes, the tabs and the reports; every job runs in the program's worker.
'use strict';

const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k === 'text') e.textContent = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'html') e.innerHTML = v;
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    e.appendChild(typeof kid === 'string' ? document.createTextNode(kid) : kid);
  }
  return e;
}

function mb(n) { return (n / 1e6).toFixed(n >= 1e8 ? 0 : 1) + ' MB'; }
function clock(s) { s = Math.floor(s); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }
function base(path) { return (path || '').split(/[\\/]/).pop(); }
const web = () => !!(state.hello && state.hello.web);
const WEB_LABELS = { 'Show in folder': 'Download the map', 'Show the report': 'Download the report' };
const showLabel = what => web() ? WEB_LABELS[what] || 'Download' : what;
const folderButton = (path, what) => el('button', { class: 'btn', text: showLabel(what || 'Show in folder'),
  onclick: () => api().open_folder(path) });
function status(text) {
  state.say = text;
  state.sayAt = Date.now();
  renderCat();
  setTimeout(renderCat, 10500);
}

function toast(text, opts) {
  opts = opts || {};
  const t = el('div', { class: 'toast' + (opts.bad ? ' bad' : '') }, el('div', { text }));
  if (opts.actions) t.appendChild(el('div', { class: 'act' }, opts.actions.map(([label, fn]) =>
    el('button', { class: 'btn small', text: label, onclick: () => { t.remove(); fn(); } }))));
  $('#toasts').appendChild(t);
  if (!opts.sticky) setTimeout(() => t.remove(), opts.ms || 6000);
  return t;
}

function dialog(title, body, buttons) {
  return new Promise(resolve => {
    const box = el('div', { class: 'dialog' }, el('h2', { text: title }), body,
      el('div', { class: 'buttons' }, (buttons || [['Close', null]]).map(([label, value, primary]) =>
        el('button', { class: 'btn' + (primary ? ' primary' : ''), text: label,
          onclick: () => { ov.remove(); resolve(value); } }))));
    const ov = el('div', { class: 'overlay', onclick: e => { if (e.target === ov) { ov.remove(); resolve(null); } } },
      box);
    document.body.appendChild(ov);
  });
}

function showAbout() {
  if (web()) { location.href = 'about.html'; return; }
  const h = state.hello || {};
  const repo = h.repository;
  const link = (label, url) => el('button', { class: 'btn small', text: label,
    onclick: () => api().open_url(url) });
  const body = el('div', { class: 'about' },
    el('p', { class: 'muted', translate: 'no', text: 'v' + (h.version || '?') }),
    el('h3', { text: 'What this is' }),
    el('p', { text: 'Devo\'s Map Doctor opens protected Warcraft III maps, fixes what stops them on Reforged 3.0, ' +
      'prepares them for the World Editor and ports the maps of the KK and M16 platforms. It also adds cheat packs ' +
      'and quality of life edits, translates maps and finds out why a map fails in the game (Diagnose). The window is ' +
      'in English and 16 other languages.' }),
    el('h3', { text: 'Privacy' }),
    el('ul', {},
      el('li', { text: 'Everything runs on this computer: your maps are never sent anywhere, and the original map is ' +
        'never written.' }),
      el('li', { text: 'When it opens, the program asks GitHub whether a new version is out. The file name index and ' +
        'the data of the old game versions are downloaded only when they are needed and you accept.' }),
      el('li', { text: '"Report a problem" opens a GitHub issue in your browser with the report filled in: you read ' +
        'it and decide whether to send it.' })),
    el('h3', { text: 'The command line' }),
    el('p', { text: 'Every action also runs from a terminal: doctor --help lists them. On Windows, doctor.exe appears next to ' +
      'the program the first time you open it; on Linux the program takes the commands itself.' }),
    el('h3', { text: 'Licenses' }),
    el('p', { text: 'The Doctor is open source under the MIT license. The parts of other projects it carries and ' +
      'their licenses are listed in THIRD_PARTY_NOTICES.txt (THIRD_PARTY_NOTICES-linux.txt on Linux), in each ' +
      'release.' }),
    el('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;margin-top:6px' },
      repo ? link('Project page', 'https://github.com/' + repo) : null,
      repo ? link('Releases', 'https://github.com/' + repo + '/releases') : null,
      link('Use it in the browser', 'https://doctor.devoltz.party')));
  dialog('About Devo\'s Map Doctor', body);
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch (e) { }
  const ta = el('textarea', {}, text);
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand('copy');
  ta.remove();
  return ok;
}

function rgbaCanvas(img, maxSide) {
  const c = el('canvas', { width: img.width, height: img.height });
  const bytes = Uint8ClampedArray.from(atob(img.rgba), ch => ch.charCodeAt(0));
  c.getContext('2d').putImageData(new ImageData(bytes, img.width, img.height), 0, 0);
  if (maxSide && Math.max(img.width, img.height) > maxSide) c.style.width = maxSide + 'px';
  return c;
}

const state = {
  hello: null, settings: {}, map: null, open: null, jobs: {}, running: null, results: {},
  gen: 0, tabState: {}, quietJobs: new Set(), images: {}, imageData: {},
  mode: null, pane: {},
  trGroups: null, trSkip: new Set(), mtQuality: 'best',
  trImages: false, trReview: null,
  extras: { card: null, translation: null, models: null, modelNames: null, singlePlayer: null, portraits: null,
    dataPointers: null, kkTextures: null, disabledIcons: null, uabi: null, preload: null, attributes: null, gameOverrides: null, requirements: null, fdf: null, slkObjects: null, lobbyImage: null },
  cheatpacks: null, cheatPack: { id: null, options: {}, result: null },
  qol: null, qolOpt: {}, qolResult: null,
  rawcodes: null,
  recipes: null,
  editorVersion: 'reforged',
};

const api = () => window.pywebview.api;

const pendingEvents = {};

async function run(task, params, opts) {
  opts = opts || {};
  const id = await api().start(task, Object.assign({ map: state.map }, params || {},
    opts.quiet ? { quiet: true } : {}));
  const ex = (params || {}).extras || {};
  const key = task + (Object.keys(ex).length ? ':' + Object.keys(ex).filter(k => ex[k]).sort().join(',') : '');
  return new Promise((resolve, reject) => {
    state.jobs[id] = { task, key, resolve, reject, started: Date.now(), label: opts.label, quiet: opts.quiet,
      size: state.open ? state.open.size : null, path: '', seen: {}, ended: {}, count: null, rate: {} };
    if (opts.quiet) state.quietJobs.add(id);
    else showJob(id, opts.label || 'Working...');
    const early = pendingEvents[id];
    if (early) { delete pendingEvents[id]; early.forEach(ev => window.doctor.onEvent(ev)); }
  });
}

window.doctor = {
  onEvent(ev) {
    if (ev.type === 'dropped') return openMap(ev.path);
    if (ev.type === 'update') return offerUpdate(ev.release);
    if (ev.type === 'index') return offerIndex(ev.release, ev.missing);
    if (ev.type === 'index_done') return toast('The file name index is ready.');
    if (ev.type === 'index_failed') return toast('The file name index could not be downloaded: ' + ev.message,
      { bad: true });
    const job = state.jobs[ev.job];
    if (!job) {
      if (!ev.job) return;
      const list = pendingEvents[ev.job] || (pendingEvents[ev.job] = []);
      list.push(ev);
      setTimeout(() => { if (pendingEvents[ev.job] === list) delete pendingEvents[ev.job]; }, 60000);
      return;
    }
    if (ev.type === 'progress') {
      if (!job.quiet) noteScope(job, ev);
      if (!job.quiet && state.running === ev.job) {
        $('#jobLabel').textContent = ev.label + (ev.total ? ' ' + ev.done + '/' + ev.total : '');
      }
      if (job.onProgress) job.onProgress(ev.label);
      return;
    }
    delete state.jobs[ev.job];
    state.quietJobs.delete(ev.job);
    if (state.running === ev.job) hideJob();
    if (ev.type === 'result') { if (!job.quiet) learnTime(job); job.resolve(ev.data); }
    else if (ev.type === 'cancelled') job.reject({ cancelled: true, kept: !!ev.kept, output: ev.output || null });
    else job.reject({ message: ev.message, trace: ev.trace });
  },
};

let timer = null;
function showJob(id, label) {
  state.running = id;
  $('#jobLabel').textContent = label;
  $('#jobTime').textContent = '0:00';
  $('#jobCard').classList.remove('hidden');
  const t0 = Date.now();
  clearInterval(timer);
  timer = setInterval(() => { $('#jobTime').textContent = clock((Date.now() - t0) / 1000); renderCat(); }, 250);
  setBusy(true);
}

const BAR = 14;
function isPrefix(p, path) { return !p || path === p || path.startsWith(p + '/'); }

function noteScope(job, ev) {
  const now = (Date.now() - job.started) / 1000;
  const path = ev.path || '';
  if (path !== job.path) {
    for (const p of Object.keys(job.seen)) if (job.ended[p] === undefined && !isPrefix(p, path)) job.ended[p] = now;
    const parts = path ? path.split('/') : [];
    for (let i = 1; i <= parts.length; i++) {
      const p = parts.slice(0, i).join('/');
      if (job.seen[p] === undefined) job.seen[p] = now;
      else delete job.ended[p];
    }
    job.path = path;
  }
  if (ev.total) {
    const r = job.rate[path] || (job.rate[path] = { t: now, d: ev.done });
    job.count = { path, done: ev.done, total: ev.total, at: now, t0: r.t, d0: r.d };
  } else if (job.count && job.count.path !== path) job.count = null;
}

function jobMB(job) { return job.size ? Math.max(job.size / 1e6, 0.1) : 1; }

const FADE = 0.8;
function fitAdd(f, x, y) {
  const o = f || { w: 0, sx: 0, sy: 0, sxx: 0, sxy: 0 };
  return { w: o.w * FADE + 1, sx: o.sx * FADE + x, sy: o.sy * FADE + y, sxx: o.sxx * FADE + x * x,
    sxy: o.sxy * FADE + x * y };
}
function fitSecs(f, x) {
  if (!f || !(f.w > 0)) return null;
  const mx = f.sx / f.w, my = f.sy / f.w, vr = f.sxx / f.w - mx * mx, cv = f.sxy / f.w - mx * my;
  if (vr > Math.pow(0.25 * mx, 2)) {
    const b = Math.max(cv / vr, 0), a = Math.max(my - b * mx, 0);
    return a + b * x;
  }
  return my * Math.sqrt(x / Math.max(mx, 1e-6));
}

function learnTime(job) {
  const secs = (Date.now() - job.started) / 1000;
  if (secs < 1) return;
  const mb = jobMB(job);
  const timing = state.settings.timing = Object.assign({}, state.settings.timing);
  for (const k of new Set([job.key, job.task])) {
    const h = Object.assign({ n: 0, stagesv2: {}, inner: {} }, timing[k]);
    delete h.stages;
    delete h.scopes;
    const mix = (old, now) => old === undefined || old === null || !h.n ? now : old * 0.6 + now * 0.4;
    h.secs = mix(h.secs, secs);
    if (job.size) h.mbps = mix(h.mbps, secs / mb);
    const stages = Object.assign({}, h.stagesv2), inner = Object.assign({}, h.inner);
    const tops = new Set();
    for (const p of Object.keys(job.seen)) {
      const s = job.seen[p], e = job.ended[p] === undefined ? secs : job.ended[p];
      const parts = p.split('/');
      if (parts.length === 1) {
        tops.add(p);
        const old = stages[p] || {};
        stages[p] = { fit: fitAdd(old.fit, mb, e - s), order: mix(old.order, s / secs),
          occ: mix(old.occ === undefined ? 0 : old.occ, 1) };
      } else {
        const top = parts[0], ts = job.seen[top], te = job.ended[top] === undefined ? secs : job.ended[top];
        const span = Math.max(te - ts, 1e-6), old = inner[p];
        const iv = [(s - ts) / span, (e - ts) / span];
        inner[p] = old ? [mix(old[0], iv[0]), mix(old[1], iv[1])] : iv;
      }
    }
    for (const p of Object.keys(stages)) if (!tops.has(p)) stages[p] = Object.assign({}, stages[p], { occ: mix(stages[p].occ, 0) });
    h.stagesv2 = stages;
    h.inner = inner;
    h.n = Math.min(h.n + 1, 20);
    timing[k] = h;
  }
  saveSettings();
}

function stageFrac(job, h, top, stageSecs, now) {
  const parts = job.path.split('/');
  const c = job.count;
  for (let i = parts.length; i >= 1; i--) {
    const p = parts.slice(0, i).join('/');
    const iv = i === 1 ? [0, 1] : (h.inner || {})[p];
    if (!iv) continue;
    const s = iv[0], e = Math.max(iv[1], iv[0]);
    if (c && c.path === p) return s + (e - s) * c.done / c.total;
    if (stageSecs > 0) {
      const begun = job.seen[p] || 0, span = (e - s) * stageSecs;
      return s + (e - s) * (span > 0 ? Math.min((now - begun) / span, 0.95) : 0.95);
    }
    if (c && i === 1 && c.path.startsWith(top + '/')) return null;
  }
  return null;
}

function estimate(job) {
  const t = state.settings.timing || {};
  const h = t[job.key] || t[job.task];
  const now = (Date.now() - job.started) / 1000;
  const c = job.count;
  const stepLeft = c && c.done > c.d0 && c.at > c.t0 ? (c.total - c.done) * (c.at - c.t0) / (c.done - c.d0) : null;
  const stepOnly = () => (c ? { frac: c.done / c.total, left: stepLeft, step: true } : null);
  if (!h || !h.stagesv2) return stepOnly();
  const mb = jobMB(job), stages = h.stagesv2;
  const top = job.path ? job.path.split('/')[0] : '';
  const st = stages[top];
  const begun = top ? job.seen[top] || 0 : 0;
  let curLeft;
  if (st) {
    const secs = fitSecs(st.fit, mb) || 0;
    const f = stageFrac(job, h, top, secs, now);
    const sofar = now - begun;
    if (f !== null && f > 0.05) {
      curLeft = Math.max((sofar > secs || !(secs > 0) ? sofar / f : (secs + 2 * sofar / f) / 3) - sofar, 0);
    }
    else curLeft = Math.max(secs - sofar, sofar * 0.25, secs * 0.05);
  } else {
    curLeft = Math.max(now - begun, 1);
  }
  if (stepLeft !== null && c.path.startsWith(top + '/')) curLeft = Math.max(curLeft, stepLeft);
  const here = st ? st.order : (now / Math.max(h.secs || now, 1e-6));
  let after = 0;
  for (const [p, s] of Object.entries(stages)) {
    if (p === top || job.seen[p] !== undefined || !(s.order > here)) continue;
    after += (s.occ === undefined ? 1 : s.occ) * (fitSecs(s.fit, mb) || 0);
  }
  let whole = 0;
  for (const s of Object.values(stages)) whole += (s.occ === undefined ? 1 : s.occ) * (fitSecs(s.fit, mb) || 0);
  let took = Math.max(whole * 0.2, 4), expected = took;
  for (const [p, s] of Object.entries(stages)) {
    if (p === top || job.seen[p] === undefined || job.ended[p] === undefined) continue;
    took += job.ended[p] - job.seen[p];
    expected += fitSecs(s.fit, mb) || 0;
  }
  const k = Math.min(Math.max(took / expected, 0.33), 3);
  const left = curLeft + after * k;
  if (!(left >= 0) || !isFinite(left)) return stepOnly();
  const frac = Math.min(Math.max(now / (now + left), 0), 0.99);
  return { frac, left };
}

function advanceShown(job, frac, left, now) {
  const prev = job.shown || 0, dt = Math.max(now - (job.shownAt === undefined ? now : job.shownAt), 0);
  job.shownAt = now;
  if (frac >= prev) return (job.shown = frac);
  const step = left > 0 ? (0.99 - prev) * Math.min(dt / (left + dt), 1) : 0;
  return (job.shown = Math.min(prev + step, 0.99));
}

function renderCat() {
  const line = $('#catline');
  const job = state.running && state.jobs[state.running];
  if (!job) {
    const fresh = state.say && state.say !== 'Ready.' && Date.now() - (state.sayAt || 0) < 10000;
    line.textContent = fresh ? state.say.replace(/\.$/, '').toLowerCase() : 'idle';
    return;
  }
  const now = (Date.now() - job.started) / 1000;
  const e = estimate(job);
  let bar, tail;
  if (e) {
    if (e.step) {
      const same = job.stepShown && job.count && job.stepShown.path === job.count.path;
      e.frac = Math.max(same ? job.stepShown.frac : 0, e.frac);
      if (job.count) job.stepShown = { path: job.count.path, frac: e.frac };
    } else e.frac = advanceShown(job, e.frac, e.left, now);
    const full = Math.round(e.frac * BAR);
    bar = '[' + '\u2588'.repeat(full) + '\u2591'.repeat(BAR - full) + '] ' + Math.round(e.frac * 100) + '%';
    tail = e.left === null || e.left === undefined ? clock(now) + ' so far' :
      e.left >= 1 ? '~' + clock(e.left) + (e.step ? ' left in this step' : ' left') : 'almost done';
  } else {
    const span = BAR - 3, k = Math.floor(now * 6) % (2 * span), at = k < span ? k : 2 * span - k;
    bar = '[' + '\u2591'.repeat(at) + '\u2588\u2588\u2588' + '\u2591'.repeat(span - at) + ']';
    tail = clock(now) + ' so far';
  }
  line.textContent = 'working\n' + bar + '\n' + tail;
}

function hideJob() {
  state.running = null;
  clearInterval(timer);
  $('#jobCard').classList.add('hidden');
  setBusy(false);
}
function setBusy(busy) {
  $$('.needs-idle').forEach(b => { b.disabled = busy || b.hasAttribute('data-off'); });
  $('#btnOpen').disabled = busy;
  $('#cat').classList.toggle('awake', busy);
  renderCat();
}

function failed(e, what) {
  if (e && e.cancelled) {
    status('Cancelled.');
    if (e.kept) toast(what + ' was cancelled. The map without the extras was saved as ' + base(e.output) + '.',
      e.output ? { actions: [[showLabel('Show in folder'), () => api().open_folder(e.output)]] } : {});
    else toast(what + ' was cancelled. Nothing was saved.');
    return;
  }
  status(what + ' failed.');
  const msg = (e && e.message) || String(e);
  state.lastError = { what, message: msg, trace: e && e.trace };
  toast(what + ' failed: ' + msg, { bad: true, sticky: true, actions: [['Report a problem', reportProblem]] });
}

async function saveSettings() { try { await api().save_settings(state.settings); } catch (e) { } }

function remember(path) {
  const r = (state.settings.recent || []).filter(p => p !== path);
  r.unshift(path);
  state.settings.recent = r.slice(0, 8);
  saveSettings();
}

function showRecent() {
  const r = state.settings.recent || [];
  $('#recent').classList.toggle('hidden', !r.length);
  $('#recentList').replaceChildren(...r.map(p => el('li', {}, el('a', { text: base(p), title: p,
    onclick: () => openMap(p) }), el('span', { class: 'faint', text: '  ' + p }))));
}

async function pickMap() {
  if (state.running) return;
  const p = await api().pick_map();
  if (p) openMap(p);
}

async function openMap(path) {
  if (state.running) { toast('Wait for the current job to finish, or cancel it.'); return; }
  const gen = ++state.gen;
  for (const id of state.quietJobs) api().cancel(id);
  state.quietJobs.clear();
  state.map = path;
  state.open = null;
  state.lastError = null;
  state.card = state.files = state.reforged = null;
  state.gameCheck = null;
  state.images = {};
  state.imageData = {};
  state.results = {};
  state.portResult = null;
  state.portPackages = [];
  state.extras = { card: null, translation: null, models: null, modelNames: null, singlePlayer: null, portraits: null,
    dataPointers: null, kkTextures: null, disabledIcons: null, uabi: null, preload: null, attributes: null, gameOverrides: null, requirements: null, fdf: null, slkObjects: null, lobbyImage: null };
  state.cheatpacks = null;
  state.cheatPack = { id: null, options: {}, result: null };
  state.qol = null;
  state.qolOpt = {};
  state.qolResult = null;
  state.trGroups = null;
  state.trSkip = new Set();
  state.rawcodes = null;
  state.recipes = null;
  state.editorVersion = 'reforged';
  state.diag = { mode: 'entry', result: null, logs: null, log: null, crashes: null, crash: null, checkMap: true };
  TABS.forEach(n => setTabState(n, 'wait'));
  $('#welcome').classList.add('hidden');
  $('#mapview').classList.remove('hidden');
  $('#btnOpen').classList.remove('hidden');
  $('#mapTitle').textContent = base(path);
  $('#mapPath').textContent = path;
  $('#badges').replaceChildren(el('span', { class: 'badge', text: 'Checking...' }));
  $('#diagLines').replaceChildren();
  $$('.tab').forEach(t => { if (!ACTIONS[t.id.slice(4)]) t.replaceChildren(); });
  Object.keys(ACTIONS).forEach(a => { $('#action-' + a).replaceChildren(); $('#results-' + a).replaceChildren(); });
  state.pane = {};
  $('#app').classList.add('hasmap');
  selectTab('fix');
  const ctx = $('#thumb').getContext('2d');
  ctx.clearRect(0, 0, 96, 96);
  status('Checking the map...');
  try {
    const r = await run('open', {}, { label: 'Checking the map...' });
    if (gen !== state.gen) return;
    state.open = r;
    remember(path);
    renderHeader();
    renderActions();
    status('Ready.');
    if (r.summary.package) { openPackage(gen); return; }
    renderTranslation();
    renderCompare();
    renderPort();
    renderDiagnose();
    setTabState('translation', 'ready');
    setTabState('compare', 'ready');
    setTabState('port', 'ready');
    setTabState('diagnose', 'ready');
    loadDiagnoseLists(gen);
    loadThumb(gen);
    checkReforgedQuietly(gen);
    loadTabsInBackground(gen);
  } catch (e) {
    if (gen !== state.gen) return;
    $('#badges').replaceChildren(el('span', { class: 'badge bad', text: 'Could not check the map' }));
    TABS.forEach(n => { tabBody(n, el('div', { class: 'card muted', text: 'The map could not be checked.' }));
      setTabState(n, 'failed'); });
    failed(e, 'Checking the map');
  }
}

function openPackage(gen) {
  for (const n of TABS) {
    if (n === 'files') continue;
    tabBody(n, el('div', { class: 'card muted', text: PACKAGE_NOTE }));
    setTabState(n, 'ready');
  }
  loadFiles(gen).then(() => { if (gen === state.gen && state.tabState.files === 'ready') selectTab('files'); });
}
const PACKAGE_NOTE = 'This is an art package, not a map: only its files can be seen and extracted (Inspect, Files).';

function renderHeader() {
  const o = state.open, s = o.summary;
  $('#mapTitle').textContent = o.name;
  $('#mapPath').textContent = o.map + '  (' + mb(o.size) + ')';
  const b = [];
  if (s.package) {
    const pk = s.package_info || {};
    b.push(el('span', { class: 'badge info', text: 'Art package' }));
    b.push(el('span', { class: 'badge', text: pk.files + ' files, ' + pk.models + ' models, ' + pk.images +
      ' images' }));
    $('#badges').replaceChildren(...b);
    $('#diagLines').replaceChildren(reportLines(o.lines));
    return;
  }
  b.push(s.protected ? el('span', { class: 'badge warn', text: 'Protected' }) :
    el('span', { class: 'badge good', text: 'No MPQ protection' }));
  b.push(s.editor_ready ? el('span', { class: 'badge good', text: 'Opens in the World Editor' }) :
    el('span', { class: 'badge warn', text: 'Needs work for the World Editor' }));
  if (s.slk.length) b.push(el('span', { class: 'badge info', text: 'SLK mode' }));
  if (s.data_problems) b.push(el('span', { class: 'badge warn', text: s.data_problems + ' Warcraft III 3.0 data ' +
    (s.data_problems === 1 ? 'problem' : 'problems') }));
  if (s.script) b.push(el('span', { class: 'badge', text: 'Script: ' + (s.script_label || s.script) }));
  if (s.campaign) b.push(el('span', { class: 'badge info', text: 'Campaign' }));
  b.push(el('span', { class: 'badge', id: 'reforgedBadge', text: 'Runs on Reforged? checking...' }));
  $('#badges').replaceChildren(...b);
  $('#diagLines').replaceChildren(reportLines(o.lines));
}

function reportLines(lines) {
  return el('div', { class: 'report' }, lines.map(([style, text]) => el('div', { class: 'l ' + style, text })));
}

function imageOf(which) {
  if (!state.images[which]) {
    state.images[which] = run('card_image', { which }, { quiet: true }).catch(() => null);
  }
  return state.images[which];
}

async function loadThumb(gen) {
  const img = await imageOf('minimap');
  if (gen !== state.gen || !img) return;
  const c = rgbaCanvas(img);
  const ctx = $('#thumb').getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(c, 0, 0, 96, 96);
}

async function checkReforgedQuietly(gen) {
  try {
    const r = await run('reforged', {}, { quiet: true });
    if (gen !== state.gen) return;
    state.reforged = r;
    const v = { 'v-yes': ['good', 'Runs on Reforged'], 'v-probably': ['info', 'Probably runs on Reforged'],
      'v-no': ['bad', 'Does not run on Reforged as it is'], 'v-unknown': ['', 'Runs on Reforged? unknown'] }[r.verdict_code] ||
      ['', 'Runs on Reforged? unknown'];
    const badge = $('#reforgedBadge');
    if (badge) { badge.className = 'badge ' + v[0]; badge.textContent = v[1]; badge.style.cursor = 'pointer';
      badge.onclick = () => selectTab('reforged'); }
    renderReforged();
    setTabState('reforged', 'ready');
    const sp = r.single_player;
    if (sp && sp.found) { state.extras.singlePlayer = sp; renderActions(); }
    if (r.models && r.models.fixable) { state.extras.models = r.models; renderActions(); }
    if (r.portraits && r.portraits.fixable) { state.extras.portraits = r.portraits; renderActions(); }
    if (r.data_pointers && r.data_pointers.fixable) { state.extras.dataPointers = r.data_pointers; renderActions(); }
    if (r.kk_textures && r.kk_textures.fixable) { state.extras.kkTextures = r.kk_textures; renderActions(); }
    if (r.disabled_icons && r.disabled_icons.fixable) { state.extras.disabledIcons = r.disabled_icons; renderActions(); }
    if (r.uabi && r.uabi.distinct) { state.extras.uabi = r.uabi; renderActions(); }
    if (r.preload && (r.preload.units || r.preload.abilities)) { state.extras.preload = r.preload; renderActions(); }
    if (r.model_names && r.model_names.fixable) { state.extras.modelNames = r.model_names; renderActions(); }
    if (r.attributes && r.attributes.fixable) { state.extras.attributes = r.attributes; renderActions(); }
    if (r.game_overrides && r.game_overrides.count) { state.extras.gameOverrides = r.game_overrides; renderActions(); }
    if (r.requirements && r.requirements.fixable) { state.extras.requirements = r.requirements; renderActions(); }
    if (r.fdf && r.fdf.fixable) { state.extras.fdf = r.fdf; renderActions(); }
    if (r.slk_objects && r.slk_objects.fixable) { state.extras.slkObjects = r.slk_objects; renderActions(); }
    if (r.lobby_image && r.lobby_image.ready) { state.extras.lobbyImage = r.lobby_image; renderActions(); }
  } catch (e) {
    if (gen !== state.gen) return;
    const badge = $('#reforgedBadge');
    if (badge) badge.textContent = 'Runs on Reforged? could not check';
    tabFailed('reforged', 'Checking whether it runs on Reforged', e);
  }
}

const ACTIONS = {
  fix: { title: 'Fix map', suffix: '_fixed', label: 'Fixing the map...',
    lead: 'Saves a copy without the protection and with the 3.0 fixes.' },
  editor: { title: 'Open in World Editor', suffix: '_editor',
    label: 'Preparing the map for the World Editor...',
    lead: 'Saves a copy the World Editor opens, triggers back as GUI.' },
};
const EXTRA_STEPS = {
  fix: ['attributes', 'gameOverrides', 'models', 'modelNames', 'portraits', 'dataPointers', 'kkTextures',
    'disabledIcons', 'uabi', 'preload', 'singlePlayer', 'card', 'translation', 'requirements', 'fdf', 'nullHandles',
    'minify', 'stripIndent', 'shrinkModels', 'shrinkModelsLossy', 'shrink', 'shrinkLossy', 'slkObjects',
    'lobbyImage'],
  editor: ['singlePlayer', 'card', 'translation', 'stripIndent'],
};

const STRIP_INDENT = { title: 'Remove the script indentation',
  detail: 'The spaces and tabs at the start of each script line go: a smaller script, the same code.' };
function stripIndentOn() { return state.settings.stripIndent === true; }
function setStripIndent(on) { state.settings.stripIndent = !!on; saveSettings(); }
function stripIndentItem() {
  return optionItem({ checked: stripIndentOn(), title: STRIP_INDENT.title, detail: STRIP_INDENT.detail,
    onchange: e => setStripIndent(e.target.checked) });
}

function choices(action) {
  const saved = state.settings.remember !== false ? ((state.settings.last || {})[action] || {}) : {};
  const out = {};
  for (const s of state.open.steps.filter(x => x.action === action)) {
    out[s.key] = s.locked ? s.applies : (s.applies && (s.key in saved ? saved[s.key] : s.on));
  }
  return out;
}

function extraSteps(action) {
  const x = state.extras, out = [];
  for (const k of EXTRA_STEPS[action]) {
    if (k === 'models' && x.models) out.push({ key: 'x:models', label: 'Fix the models that crash the game',
      detail: x.models.fixable + ' imported ' + (x.models.fixable === 1 ? 'model has' : 'models have') +
        ' a problem the Doctor can fix.', on: true, applies: true, group: 'extra' });
    if (k === 'modelNames' && x.modelNames) out.push({ key: 'x:modelNames',
      label: 'Give the models their name back',
      detail: x.modelNames.fixable + ' model ' + (x.modelNames.fixable === 1 ? 'name carries' :
        'names carry') + ' the suffix the "Model_Encrypt" tool adds (体): they are renamed back.',
      on: true, applies: true, group: 'extra' });
    if (k === 'portraits' && x.portraits) out.push({ key: 'x:portraits', label: 'Fix black portraits',
      detail: x.portraits.fixable + ' portrait ' + (x.portraits.fixable === 1 ? 'model has' : 'models have') +
        ' an old camera that shows black in 3.0; it is removed. Check in game.',
      on: false, applies: true, group: 'extra' });
    if (k === 'portraits' && x.portraits) {
      out.push({ key: 'x:portraitStamp', label: '... and stamp the model version 1800 (test)',
        detail: 'With "Fix black portraits": also writes the portrait models as version 1800. Untested in game: try ' +
          'one hero first.', on: false, applies: true, group: 'extra' });
      out.push({ key: 'x:portraitUpgrade', label: '... and widen the layout to the 3.0 one (test)',
        detail: 'With "Fix black portraits": the version 1800 and the fields the 3.0 models have. Untested in game: ' +
          'try one hero first.', on: false, applies: true, group: 'extra' });
    }
    if (k === 'dataPointers' && x.dataPointers) out.push({ key: 'x:dataPointers', label: 'Fix the levelled data pointers',
      detail: x.dataPointers.fixable + ' levelled ' + (x.dataPointers.fixable === 1 ? 'field points' : 'fields point') +
        ' to another data column on some levels.', on: true, applies: true, group: 'extra' });
    if (k === 'kkTextures' && x.kkTextures) out.push({ key: 'x:kkTextures',
      label: 'Decrypt the KK textures',
      detail: x.kkTextures.fixable + (x.kkTextures.fixable === 1 ? ' texture is' : ' textures are') +
        ' encrypted by the KK platform (BLX1): the game shows the models without them and the icons green.',
      on: true, applies: true, group: 'extra' });
    if (k === 'disabledIcons' && x.disabledIcons) out.push({ key: 'x:disabledIcons',
      label: 'Fix the green icons',
      detail: x.disabledIcons.fixable + ' imported ' + (x.disabledIcons.fixable === 1 ? 'icon has' : 'icons have') +
        ' no disabled art, so the game draws it green (a dead hero, another unit\'s items); it is made from each icon.',
      on: true, applies: true, group: 'extra' });
    if (k === 'uabi' && x.uabi) out.push({ key: 'x:uabi', label: 'Move the unit ability lists to the script',
      detail: x.uabi.distinct + ' distinct abilities in the unit lists; reported to drop games on ' +
        'Reforged. Test it before sharing.', on: false, applies: true, group: 'extra' });
    if (k === 'preload' && x.preload) out.push({ key: 'x:preload',
      label: 'Load the first seconds under the loading screen',
      detail: x.preload.units + ' unit types and ' + x.preload.abilities +
        ' abilities are loaded before play starts, so the game does not freeze.',
      on: false, applies: true, group: 'extra' });
    if (k === 'singlePlayer' && x.singlePlayer) out.push({ key: 'x:singlePlayer',
      label: 'Let it run in single player',
      detail: 'The map ends the game when played alone.',
      on: false, applies: true, group: 'extra' });
    if (k === 'card' && x.card) out.push({ key: 'x:card', label: 'Apply the map card changes',
      detail: Object.keys(x.card).length + ' changed in the Map card tab.', on: true, applies: true, group: 'extra' });
    if (k === 'translation' && x.translation && !x.translation.check.error) out.push({ key: 'x:translation',
      label: 'Apply the translation',
      detail: base(x.translation.file) + ', from the Translation tab.', on: true, applies: true, group: 'extra' });
    if (k === 'attributes' && x.attributes) out.push({ key: 'x:attributes', label: 'Redo the file checksums',
      detail: x.attributes.fixable + ' file checksums in (attributes) no longer match, and the game can refuse the map as ' +
        'corrupted.', on: true, applies: true, group: 'extra' });
    if (k === 'gameOverrides' && x.gameOverrides) out.push({ key: 'x:gameOverrides',
      label: 'Remove map files that replace the game\'s own',
      detail: x.gameOverrides.count + ' images and models of the map have the path of a game file, and the game has ' +
        'closed on maps that ship them. A map can replace an icon on purpose, so this is off by default. Needs the ' +
        'game installed.',
      on: false, applies: true, group: 'extra' });
    if (k === 'requirements' && x.requirements) out.push({ key: 'x:requirements',
      label: 'Unlock abilities that require a tech the map lacks',
      detail: x.requirements.fixable + ' abilities inherit a requirement that only the 3.0 game data has and the map ' +
        'does not define: an empty requirement is written.', on: true, applies: true, group: 'extra' });
    if (k === 'fdf' && x.fdf) out.push({ key: 'x:fdf', label: 'Fix frame file lists',
      detail: 'Adds the final line break a .toc needs, so the game reads its last frame file.',
      on: true, applies: true, group: 'extra' });
    const jass = /jass/.test((state.open && state.open.summary && state.open.summary.script) || '');
    if (k === 'nullHandles' && jass) out.push({ key: 'x:nullHandles', label: 'Null handle locals',
      detail: 'Writes the missing set x = null before each return and at the end of the functions of the script, so ' +
        'handle ids can be recycled (pjass checks the result).', on: false, applies: true, group: 'extra' });
    if (k === 'minify' && jass) out.push({ key: 'x:minify', label: 'Minify script',
      detail: 'Shrinks war3map.j: no comments, short names, dead functions and globals removed, constants written in ' +
        'place (pjass checks the result). Readable names are lost.', on: false, applies: true, group: 'extra' });
    if (k === 'shrinkModels') out.push({ key: 'x:shrinkModels', label: 'Shrink models (lossless)',
      detail: 'Removes repeated animation keys from the imported models; each model is read back and compared.', on: false, applies: true, group: 'extra' });
    if (k === 'shrinkModelsLossy') out.push({ key: 'x:shrinkModelsLossy', label: 'Shrink models, lossy',
      detail: 'Also drops animation keys that change a movement by less than 0.05 units or a rotation by less than ' +
        '0.002 rad; the first and last key of every sequence stay.', on: false, applies: true, group: 'extra' });
    if (k === 'slkObjects' && x.slkObjects) out.push({ key: 'x:slkObjects',
      label: 'Make the editor object files from the SLK tables',
      detail: 'A map optimized into SLK/TXT files has no unit, item or ability data the World Editor reads; this ' +
        'writes it (war3map.w3u/w3t/w3a) from the tables, the parents of units and items inferred. Needs the game ' +
        'installed.', on: false, applies: true, group: 'extra' });
    if (k === 'lobbyImage' && x.lobbyImage) out.push({ key: 'x:lobbyImage', label: 'Use my own lobby image',
      detail: 'Asks for a picture: it becomes the lobby image (war3mapMap.blp), the minimap moves to ' +
        'war3mapMap_ingame.blp and the script puts it back in game. Not tested in game.', on: false, applies: true, group: 'extra' });
    if (k === 'stripIndent') out.push({ key: 'x:stripIndent', label: STRIP_INDENT.title, detail: STRIP_INDENT.detail,
      on: stripIndentOn(), applies: true, group: 'extra' });
    if (k === 'shrink') out.push({ key: 'x:shrink', label: 'Make the map smaller, losing nothing',
      detail: 'Recompresses every file and stores duplicates once. Slow on big maps.',
      on: false, applies: true, group: 'extra' });
    if (k === 'shrinkLossy') out.push({ key: 'x:shrinkLossy', label: 'If still above 512 MiB, make the art smaller',
      detail: 'Halves the biggest textures and makes WAV sounds mono at 22 kHz, only until the map fits the game\'s ' +
        '512 MiB. This loses quality; the map is shrunk losing nothing first.',
      on: false, applies: true, group: 'extra' });
  }
  return out;
}

function renderActions() {
  if (!state.open) return;
  for (const action of Object.keys(ACTIONS)) $('#action-' + action).replaceChildren(renderAction(action));
}

const FLAGS = { mpq: 'unprotect', falsos: 'fake-files', fake_list: 'fake-files', lista: 'listfile',
  listing: 'listfile', ids: 'ids', desprotecao: 'unprotect', unprotection: 'unprotect', script_de_volta: 'script-back',
  script_restore: 'script-back', arquivos_do_editor: 'editor-files', editor_only_files: 'editor-files',
  contagem_inflada: 'counts', inflated_counts: 'counts', doodads_invalidos: 'doodads', invalid_doodads: 'doodads',
  gatilhos_gui: 'gui-triggers', objetos_do_script: 'script-objects', unidades_seguras: 'safe-units', 'x:models': 'models', 'x:modelNames': 'model-names', 'x:portraits': 'portraits',
  'x:dataPointers': 'data-pointers', 'x:kkTextures': 'kk-textures', 'x:disabledIcons': 'green-icons',
  'x:uabi': 'uabi', 'x:preload': 'preload', 'x:singlePlayer': 'single-player', 'x:card': 'card',
  'x:translation': 'translation', 'x:stripIndent': 'strip-indent', 'x:shrink': 'shrink',
  'x:shrinkLossy': 'shrink-lossy', 'x:attributes': 'fix-attributes', 'x:gameOverrides': 'remove-game-files',
  'x:requirements': 'fix-requirements', 'x:fdf': 'fix-fdf', 'x:nullHandles': 'null-handles', 'x:minify': 'minify',
  'x:slkObjects': 'slk-objects', 'x:lobbyImage': 'lobby-image', 'x:shrinkModels': 'shrink-models',
  'x:shrinkModelsLossy': 'shrink-models-lossy', 'x:portraitStamp': 'portraits=stamp',
  'x:portraitUpgrade': 'portraits=upgrade' };

function shellLine(action) {
  const card = $('.action[data-action="' + action + '"]');
  if (!card) return;
  const flags = [];
  for (const box of $$('input[data-key]', card)) {
    if (!box.checked) continue;
    const k = box.dataset.key;
    let f = /^(dados|data):/.test(k) ? 'data' : FLAGS[k] || k.replace(/^x:/, '').replace(/[:_]/g, '-');
    if (k === 'x:translation' && state.extras.translation) f += '="' + base(state.extras.translation.file) + '"';
    if (!flags.includes(f)) flags.push(f);
  }
  const name = state.open ? state.open.name : base(state.map);
  if (action === 'editor' && state.editorVersion !== 'reforged') flags.push(['editor-version', state.editorVersion].join('='));
  $('.shell .cmd', card).textContent = 'doctor ' + action + ' "' + name + '"' +
    flags.map(f => ' --' + f).join('');
}

function editorVersionRow() {
  const ev = state.open.editor_version || {};
  const versions = ev.available || [];
  if (!versions.length) return null;
  const guess = ev.guess;
  const sel = el('select', { class: 'field', style: 'width:auto', 'data-editor-version': '1',
    title: 'The World Editor that will open the map: Reforged, or the one of the map\'s own version, which keeps it.',
    onchange: e => { state.editorVersion = e.target.value; shellLine('editor'); } },
    el('option', { value: 'reforged', text: 'Reforged (3.0)' }),
    versions.map(v => el('option', { value: v, text: v })));
  sel.value = versions.includes(state.editorVersion) ? state.editorVersion : 'reforged';
  return el('div', { class: 'row', style: 'gap:8px;align-items:center;margin:4px 0 8px' },
    el('span', { text: 'World Editor' }), sel,
    guess ? el('span', { class: 'muted' }, el('span', { text: 'Made for World Editor' }), ' ',
      el('span', { class: 'mono', text: guess })) : null,
    ev.saved_by ? el('span', { class: 'faint', translate: 'no', text: '(' + ev.saved_by + ')' }) : null);
}

function renderAction(action) {
  const a = ACTIONS[action];
  if (state.open.summary.package) {
    return el('div', { class: 'card action', 'data-action': action }, el('div', { class: 'head' },
      el('h2', { text: a.title })), el('p', { class: 'muted', text: 'Nothing to do: this is an art package, not a map.' }),
    el('div', { class: 'foot' }, el('button', { class: 'btn primary', text: 'Show its files',
      onclick: () => selectTab('files') })));
  }
  const picked = choices(action);
  const steps = state.open.steps.filter(x => x.action === action);
  const extras = extraSteps(action);
  const showNa = !!(state.settings.showNa || {})[action];
  const list = el('ul', { class: 'steps' });
  const groups = [['main', null], ['data', 'Warcraft III 3.0 data'], ['extra', 'Extras']];
  for (const [g, title] of groups) {
    const items = steps.filter(s => s.group === g && (s.applies || showNa)).concat(extras.filter(s => s.group === g));
    if (!items.length) continue;
    if (title) list.appendChild(el('li', { class: 'grouptitle', text: title }));
    for (const s of items) list.appendChild(stepItem(action, s, s.key.startsWith('x:') ? s.on : picked[s.key]));
  }
  const hidden = steps.filter(s => !s.applies).length;
  const any = steps.some(s => s.applies) || extras.length;
  const card = el('div', { class: 'card action', 'data-action': action },
    el('div', { class: 'head' }, el('h2', { text: a.title }),
      presetMenu(action)),
    el('p', { class: 'lead', text: a.lead }),
    action === 'editor' ? editorVersionRow() : null,
    any ? list : el('p', { class: 'muted', text: 'Nothing to do here for this map.' }),
    el('div', { class: 'foot' },
      el('button', { class: 'btn primary needs-idle', text: a.title, disabled: !any || !!state.running,
        'data-off': !any, onclick: () => runAction(action) }),
      hidden ? el('label', { class: 'show-na' }, el('input', { type: 'checkbox', checked: showNa, onchange: e => {
        state.settings.showNa = Object.assign({}, state.settings.showNa, { [action]: e.target.checked });
        saveSettings(); renderActions(); } }), ' show the ' + hidden + ' steps not needed') : null),
    any ? el('div', { class: 'shell' }, '$ ', el('span', { class: 'cmd' }), el('span', { class: 'cursor' })) : null);
  if (any) setTimeout(() => shellLine(action));
  return card;
}

function stepItem(action, s, checked) {
  const locked = s.locked && s.applies;
  const box = el('input', { type: 'checkbox', checked: !!checked, disabled: locked || !s.applies,
    'data-key': s.key, onchange: () => {
      if (s.key === 'x:stripIndent') setStripIndent(box.checked);
      rememberChoice(action); shellLine(action); } });
  return el('li', { class: 'step' + (locked ? ' locked' : '') + (s.applies ? '' : ' na') },
    box, el('div', {}, el('div', { class: 't', text: s.label }),
      s.detail ? el('div', { class: 'd', text: s.detail }) : null,
      s.why && (locked || !s.applies) ? el('div', { class: 'why', text: s.why }) : null));
}

function readChoices(action) {
  const card = $('.action[data-action="' + action + '"]');
  const options = {}, extras = {};
  for (const box of $$('input[data-key]', card)) {
    const k = box.dataset.key;
    if (k.startsWith('x:')) extras[k.slice(2)] = box.checked;
    else options[k] = box.checked;
  }
  return { options, extras };
}

function rememberChoice(action) {
  if (state.settings.remember === false) return;
  const { options } = readChoices(action);
  state.settings.last = Object.assign({}, state.settings.last, {
    [action]: Object.assign({}, (state.settings.last || {})[action], options) });
  saveSettings();
}

function presetMenu(action) {
  const presets = (state.settings.presets || {})[action] || {};
  const sel = el('select', { class: 'field', style: 'width:auto', title: 'Presets',
    onchange: async e => {
      const v = e.target.value;
      e.target.value = '';
      if (v === '__default') {
        if (state.settings.last) delete state.settings.last[action];
        saveSettings(); renderActions();
      } else if (v === '__save') {
        const name = await askText('Save these choices as a preset', 'Name');
        if (!name) return;
        state.settings.presets = Object.assign({}, state.settings.presets);
        state.settings.presets[action] = Object.assign({}, presets, { [name]: readChoices(action).options });
        saveSettings(); renderActions(); toast('Preset "' + name + '" saved.');
      } else if (v === '__remember') {
        state.settings.remember = state.settings.remember === false;
        saveSettings(); renderActions();
      } else if (v.startsWith('p:')) {
        const p = presets[v.slice(2)] || {};
        state.settings.last = Object.assign({}, state.settings.last, { [action]: p });
        saveSettings(); renderActions();
      }
    } },
    el('option', { value: '', text: 'Presets' }),
    el('option', { value: '__default', text: 'Recommended (the defaults)' }),
    Object.keys(presets).map(n => el('option', { value: 'p:' + n, text: n })),
    el('option', { value: '__save', text: 'Save these choices...' }),
    el('option', { value: '__remember', text: (state.settings.remember === false ? 'Remember my choices' :
      'Stop remembering my choices') }));
  return sel;
}

function askText(title, label, value) {
  const input = el('input', { class: 'field', type: 'text', value: value || '' });
  const body = el('div', {}, el('div', { class: 'muted', text: label, style: 'margin-bottom:6px' }), input);
  setTimeout(() => input.focus(), 30);
  return dialog(title, body, [['Cancel', null], ['Save', '__ok', true]]).then(v => v ? input.value.trim() : null);
}

async function runAction(action) {
  if (state.running) return;
  const a = ACTIONS[action];
  const { options, extras } = readChoices(action);
  const params = { options, extras: {} };
  if (extras.models) params.extras.models = true;
  if (extras.modelNames) params.extras.model_names = true;
  if (extras.singlePlayer) params.extras.single_player = true;
  if (extras.portraits) params.extras.portraits = true;
  if (extras.dataPointers) params.extras.data_pointers = true;
  if (extras.kkTextures) params.extras.kk_textures = true;
  if (extras.disabledIcons) params.extras.disabled_icons = true;
  if (extras.uabi) params.extras.uabi = true;
  if (extras.preload) params.extras.preload = true;
  if (extras.attributes) params.extras.attributes = true;
  if (extras.gameOverrides) params.extras.game_overrides = true;
  if (extras.requirements) params.extras.requirements = true;
  if (extras.fdf) params.extras.fdf = true;
  if (extras.nullHandles) params.extras.null_handles = true;
  if (extras.minify) params.extras.minify = true;
  if (extras.slkObjects) params.extras.slk_objects = true;
  if (extras.shrinkModels || extras.shrinkModelsLossy) params.extras.shrink_models = { lossy: !!extras.shrinkModelsLossy };
  if (extras.portraits && extras.portraitUpgrade) params.extras.portraits = 'upgrade';
  else if (extras.portraits && extras.portraitStamp) params.extras.portraits = 'stamp';
  if (extras.lobbyImage) {
    const img = await api().pick_file('image');
    if (img) params.extras.lobby_image = img;
  }
  if (extras.card && state.extras.card) params.extras.card = state.extras.card;
  if (extras.translation && state.extras.translation) params.extras.translation = state.extras.translation.file;
  if (extras.stripIndent) params.extras.strip_indent = true;
  if (extras.shrink || extras.shrinkLossy) {
    params.extras.shrink = { recompress: true, blp: true, dedup: true };
    if (extras.shrinkLossy) params.extras.shrink.lossy = true;
  }
  if (action === 'editor' && state.editorVersion !== 'reforged') params.editor_version = state.editorVersion;
  status(a.label);
  try {
    const r = await run(action, params, { label: a.label });
    state.results[action] = r;
    renderResult(action, r);
    status(r.outcome === 'ok' ? 'Done.' : r.outcome === 'partial' ? 'Done, with some leftovers.' :
      r.outcome === 'nothing' ? 'Nothing to do.' : 'It did not work.');
  } catch (e) { failed(e, a.title); }
}

function renderResult(action, r) {
  const a = ACTIONS[action];
  const badge = { ok: ['good', 'Done'], partial: ['warn', 'Done, with leftovers'], nothing: ['', 'Nothing to do'],
    failed: ['bad', 'Did not work'] }[r.outcome] || ['', r.outcome];
  const ch = r.changes || { files: [], notes: [] };
  const card = el('div', { class: 'card', id: 'result-' + action },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: a.title + ': result' }),
      el('span', { class: 'badge ' + badge[0], text: badge[1] })),
    reportLines(r.lines),
    ch.files.length || ch.notes.length ? el('div', {}, el('h3', { text: 'What changed' }),
      ch.files.length ? el('div', { class: 'scroll', style: 'max-height:240px' }, el('table', { class: 'grid' },
        el('thead', {}, el('tr', {}, el('th', { text: 'File' }), el('th', { text: 'How' }), el('th', { text: 'Why' }))),
        el('tbody', {}, ch.files.map(f => el('tr', {}, el('td', { class: /[.\\(]/.test(f.file) ? 'mono' : null, text: f.file }),
          el('td', { text: f.how }), el('td', { class: 'muted', text: f.why })))))) : null,
      ch.notes.map(n => el('div', { class: 'muted', text: n }))) : null,
    el('div', { class: 'foot row', style: 'margin-top:14px' },
      r.file ? folderButton(r.file) : null,
      el('button', { class: 'btn', text: 'Copy report', onclick: async () => {
        await copyText(plainReport(r.lines)); toast('The report is in the clipboard.'); } }),
      el('button', { class: 'btn ghost', text: 'Report a problem', onclick: reportProblem })));
  const old = $('#result-' + action);
  if (old) old.replaceWith(card); else $('#results-' + action).prepend(card);
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function plainReport(lines) {
  return lines.map(([style, text]) => (style === 'title' ? '## ' : '') + text).join('\n');
}

async function reportProblem() {
  const parts = ['Version: ' + (state.hello ? state.hello.version : '?')];
  if (state.open) parts.push('Map: ' + state.open.name + ' (' + mb(state.open.size) + ')', '',
    '### Diagnosis', '```', plainReport(state.open.lines), '```');
  const otherTitles = { port: 'Port to Reforged', cheatpacks: 'Cheat pack' };
  for (const [action, r] of Object.entries(state.results)) {
    parts.push('', '### ' + (ACTIONS[action] ? ACTIONS[action].title : otherTitles[action] || action), '```',
      plainReport(r.lines || []), '```');
  }
  if (state.lastError) parts.push('', '### Error', state.lastError.what + ': ' + state.lastError.message,
    '```', (state.lastError.trace || '').slice(-2500), '```');
  parts.push('', 'What I expected, and what happened instead:', '');
  const body = parts.join('\n');
  const title = 'Problem with ' + (state.open ? state.open.name : 'the Doctor');
  const text = el('textarea', {}, body);
  const where = state.hello && state.hello.repository ? 'Opens a GitHub issue with this text; the map is ' +
    'never attached.' : 'Copy this text into your report.';
  const v = await dialog('Report a problem', el('div', {}, el('p', { class: 'muted', text: where }), text),
    [['Cancel', null], ['Copy', 'copy'], state.hello && state.hello.repository ? ['Open GitHub issue', 'gh', true] :
      null].filter(Boolean));
  if (v === 'copy') { await copyText(text.value); toast('The report is in the clipboard.'); }
  if (v === 'gh') api().report_problem(title, text.value);
}

function offerUpdate(release) {
  const v = (release.version || '').replace(/^v/i, '');
  const u = $('#update');
  u.className = 'badge info';
  u.textContent = 'Version ' + v + ' is out';
  u.style.cursor = 'pointer';
  u.onclick = async () => {
    const ok = await dialog('Update', el('p', { text: 'Version ' + v + ' is available (you have ' +
      state.hello.version + '). Install it now? The program restarts.' }),
      [['Not now', null], ['Install', true, true]]);
    if (ok) {
      status('Downloading the new version...');
      const r = await api().install_update(release);
      if (r !== true) toast('The update failed: ' + r + '. The release page opened instead.', { bad: true });
    }
  };
}

function offerIndex(release, missing) {
  toast('The file name index (names.npz, ' + mb(release.index_size || 0) + ') is ' + (missing ? 'missing' :
    'out of date') + '. It names more files in maps with damaged file tables.',
  { sticky: true, actions: [['Download', () => { api().download_index(release); toast('Downloading the index...'); }],
    ['Later', () => {}]] });
}

const TABS = ['card', 'reforged', 'files', 'script', 'cheatpacks', 'qol', 'triggers', 'translation', 'compare', 'port',
  'diagnose'];
const TAB_DATA = { card: loadCard, files: loadFiles, script: loadScript, cheatpacks: loadCheatpacks, qol: loadQol,
  triggers: loadTriggers, reforged: checkReforgedQuietly };

const MODES = { fix: ['fix', 'reforged'], editor: ['editor', 'card', 'triggers'], port: ['port'],
  cheatpacks: ['cheatpacks'], qol: ['qol'], translation: ['translation'], inspect: ['files', 'script', 'compare'],
  diagnose: ['diagnose'] };
const modeOf = name => Object.keys(MODES).find(m => MODES[m].includes(name));

function setTabState(name, st) {
  state.tabState[name] = st;
  for (const b of $$('[data-tab="' + name + '"]')) {
    b.disabled = st === 'wait';
    b.classList.toggle('loading', st === 'wait');
    b.classList.toggle('failed', st === 'failed');
    b.title = st === 'wait' ? 'Loading: the tab opens when its information is in.' :
      st === 'failed' ? 'Loading failed: open the tab to try again.' : '';
  }
}

async function loadTabsInBackground(gen) {
  const groups = loadTranslationGroups(gen);
  for (const name of ['card', 'files', 'script', 'cheatpacks', 'qol', 'triggers']) {
    if (gen !== state.gen) return;
    await TAB_DATA[name](gen);
  }
  await groups;
}

function selectTab(name) {
  if (!ACTIONS[name] && state.tabState[name] === 'wait') return;
  const mode = modeOf(name);
  state.mode = mode;
  state.pane[mode] = name;
  $$('#modes button').forEach(b => b.classList.toggle('on', b.dataset.mode === mode));
  $$('.mode').forEach(m => m.classList.toggle('hidden', m.id !== 'mode-' + mode));
  const box = $('#mode-' + mode);
  $$('.subtabs button', box).forEach(b => b.classList.toggle('on', b.dataset.tab === name));
  $$('.tab', box).forEach(t => t.classList.toggle('hidden', t.id !== 'tab-' + name));
  $('#main').scrollTop = 0;
}

function selectMode(mode) {
  if (!state.open && !state.map) return;
  const last = state.pane[mode];
  const ready = n => ACTIONS[n] || state.tabState[n] !== 'wait';
  const name = last && ready(last) ? last : MODES[mode].find(ready);
  if (name) selectTab(name);
}

function tabBody(name, ...kids) {
  $('#tab-' + name).replaceChildren(...kids.flat().filter(k => k !== null && k !== undefined && k !== false));
}
function tabFailed(name, what, e) {
  setTabState(name, 'failed');
  tabBody(name, el('div', { class: 'card' }, el('div', { class: 'report' },
    el('div', { class: 'l bad', text: what + (e && e.cancelled ? ' was cancelled.' : ' failed.') }),
    el('div', { class: 'l info', text: (e && e.message) || '' })),
  el('button', { class: 'btn small', text: 'Try again', onclick: () => {
    setTabState(name, 'wait');
    tabBody(name, el('div', { class: 'card muted', text: 'Loading again...' }));
    TAB_DATA[name](state.gen);
  } })));
}

function colored(text) {
  const out = el('div', { class: 'colorpreview', translate: 'no' });
  let color = null, buf = '';
  const flush = () => { if (buf) out.appendChild(el('span', { style: color ? 'color:#' + color : null, text: buf }));
    buf = ''; };
  for (let i = 0; i < (text || '').length; i++) {
    const rest = text.slice(i);
    let m = /^\|c[0-9a-fA-F]{2}([0-9a-fA-F]{6})/.exec(rest);
    if (m) { flush(); color = m[1]; i += 9; continue; }
    if (/^\|r/i.test(rest)) { flush(); color = null; i += 1; continue; }
    if (/^\|n/i.test(rest)) { buf += '\n'; i += 1; continue; }
    buf += text[i];
  }
  flush();
  return out;
}

const CARD_FIELDS = [
  ['name', 'Map name', 'text'], ['author', 'Author', 'text'], ['players_suggested', 'Suggested players', 'text'],
  ['description', 'Description', 'area'], ['lobby_name', 'Name in the game list', 'text'],
  ['loading.title', 'Loading screen title', 'text'], ['loading.subtitle', 'Loading screen subtitle', 'text'],
  ['loading.text', 'Loading screen text', 'area'],
  ['prologue.title', 'Prologue title', 'text'], ['prologue.subtitle', 'Prologue subtitle', 'text'],
  ['prologue.text', 'Prologue text', 'area'],
];

function getPath(obj, path) { return path.split('.').reduce((o, k) => (o || {})[k], obj); }

function cardChange(path, value) {
  const original = getPath(state.card, path);
  const ch = state.extras.card || {};
  const [a, b] = path.split('.');
  if (b) {
    ch[a] = Object.assign({}, ch[a]);
    if (value === original) delete ch[a][b]; else ch[a][b] = value;
    if (!Object.keys(ch[a]).length) delete ch[a];
  } else if (value === original) delete ch[a]; else ch[a] = value;
  state.extras.card = Object.keys(ch).length ? ch : null;
  renderActions();
}

async function loadCard(gen) {
  try {
    const [card, minimap, preview] = await Promise.all([run('card', {}, { quiet: true }), imageOf('minimap'),
      imageOf('preview')]);
    if (gen !== state.gen) return;
    state.card = card;
    state.imageData = { minimap, preview };
    renderCard();
    setTabState('card', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('card', 'Reading the map card', e); }
}

function renderCard() {
  const c = state.card;
  if (c && c.ok === false) {
    tabBody('card', el('div', { class: 'card muted', text: c.message || 'The map card cannot be read.' }));
    return;
  }
  const form = el('div', { class: 'form' });
  for (const [path, label, kind] of CARD_FIELDS) {
    const value = getPath(c, path);
    if (value === undefined || value === null) continue;
    const pending = state.extras.card && getPath(state.extras.card, path);
    const input = kind === 'area' ? el('textarea', {}, pending !== undefined && pending !== null ? pending : value) :
      el('input', { type: 'text', value: pending !== undefined && pending !== null ? pending : value });
    let preview = colored(input.value);
    const from = el('input', { type: 'color', value: '#ffcc00' }), to = el('input', { type: 'color', value: '#ff3300' });
    const grad = el('div', { class: 'gradient' }, el('span', { class: 'faint', text: 'Gradient' }), from, to,
      el('button', { class: 'btn small', text: 'Apply to the text', onclick: async () => {
        const plain = input.value.replace(/\|c[0-9a-fA-F]{8}|\|r/g, '');
        try {
          input.value = await run('gradient', { text: plain, colors: [from.value.slice(1), to.value.slice(1)] },
            { quiet: true });
          input.dispatchEvent(new Event('input'));
        } catch (e) { toast('The gradient failed: ' + (e.message || e), { bad: true }); }
      } }));
    input.addEventListener('input', () => {
      const fresh = colored(input.value);
      preview.replaceWith(fresh);
      preview = fresh;
      input.classList.toggle('changed', input.value !== value);
      cardChange(path, input.value);
    });
    input.classList.toggle('changed', input.value !== value);
    form.append(el('label', { text: label }), el('div', {}, input, preview, kind === 'text' || kind === 'area' ? grad :
      null));
  }
  const players = (c.players || []).length ? el('div', {}, el('h3', { text: 'Players' }), el('div', { class: 'form' },
    c.players.map(p => [el('label', { text: 'Player ' + (p.index + 1) + (p.race ? ' (' + p.race + ')' : '') }),
      el('input', { type: 'text', value: p.name, oninput: e => setListName('players', p, e.target) })]).flat())) : null;
  const forces = (c.forces || []).length ? el('div', {}, el('h3', { text: 'Teams' }), el('div', { class: 'form' },
    c.forces.map(f => [el('label', { text: 'Team ' + (f.index + 1) }),
      el('input', { type: 'text', value: f.name, oninput: e => setListName('forces', f, e.target) })]).flat())) : null;
  const images = el('div', { class: 'row wrap', style: 'gap:18px' },
    ['minimap', 'preview'].map(which => imageSlot(which, (c.images || {})[which])));
  const info = c.info || {};
  const chatCommandText = (list) => (list || [])
    .map(x => typeof x === 'string' ? x : String(x.text || ''))
    .map(t => t.trim()).filter(t => t).join('\n');
  const infoCard = el('div', { class: 'card' }, el('h2', { text: 'What the map says about itself' }),
    el('div', { class: 'form' },
      el('label', { text: 'Language' }), el('div', { style: 'padding-top:7px', text: describeLanguage(info.language) }),
      el('label', { text: 'Save' }), el('div', { style: 'padding-top:7px', text: describeSave(info.save) })),
    chatCommandsBox(info, chatCommandText));
  tabBody('card',
    el('div', { class: 'card' }, el('h2', { text: 'Map card' }),
      el('p', { class: 'lead', text: 'Changes go into the next copy ("Apply the map card changes" in ' +
        'Fix or Editor).' }),
      form, players, forces,
      el('h3', { text: 'Images' }), images),
    infoCard);
}

function setListName(list, item, input) {
  const ch = state.extras.card || {};
  const arr = (ch[list] || []).filter(x => x.index !== item.index);
  if (input.value !== item.name) arr.push({ index: item.index, name: input.value });
  if (arr.length) ch[list] = arr; else delete ch[list];
  input.classList.toggle('changed', input.value !== item.name);
  state.extras.card = Object.keys(ch).length ? ch : null;
  renderActions();
}

function describeLanguage(lang) {
  if (!lang) return 'unknown';
  if (typeof lang === 'string') return lang;
  return (lang.language || 'unknown') + (lang.script ? ' (' + lang.script + ' script)' : '');
}

const MATCH_TEXT = { true: 'whole message', false: 'contains', null: 'decided by the script' };
function chatCommandsBox(info, chatCommandText) {
  const list = (info.chat_commands || []).map(x => typeof x === 'string' ? { text: x, exact: true, count: 1 } : x);
  const compared = info.chat_compared || [];
  const head = el('div', { class: 'row', style: 'margin:16px 0 6px' },
    el('h3', { class: 'grow', style: 'margin:0', text: 'Chat commands' }),
    list.length ? el('span', { class: 'faint', text: list.length + (list.length === 1 ? ' command' : ' commands') }) :
      null,
    chatCommandText(list) ? el('button', { class: 'btn small ghost', text: 'Copy all', onclick: async () => {
      await copyText(chatCommandText(list));
      toast('The commands are in the clipboard, one per line.');
    } }) : null);
  if (!list.length && !compared.length) {
    return el('div', {}, head, el('p', { class: 'muted', text: 'None found in the script.' }));
  }
  const cell = x => {
    if (x.text === '') return el('td', { class: 'faint', text: '(any message)' });
    if (x.text === null || x.text === undefined) {
      return el('td', { class: 'faint' }, el('span', { class: 'mono', text: x.expr || '?' }),
        el('span', { class: 'tag', text: 'built by the script' }));
    }
    return el('td', {}, el('span', { class: 'mono cmd', text: x.text }),
      x.decoded ? el('span', { class: 'tag', text: 'decoded' }) : null);
  };
  return el('div', {}, head,
    list.length ? el('div', { class: 'scroll', style: 'max-height:360px' }, el('table', { class: 'grid chat' },
      el('thead', {}, el('tr', {}, el('th', { text: 'Command' }), el('th', { text: 'Match' }),
        el('th', { text: 'Triggers' }))),
      el('tbody', {}, list.map(x => el('tr', {}, cell(x),
        el('td', { class: 'muted', text: MATCH_TEXT[x.exact === undefined ? null : x.exact] }),
        el('td', { class: 'muted', text: String(x.count || 1) })))))) : null,
    compared.length ? el('div', { style: 'margin-top:10px' },
      el('div', { class: 'faint', style: 'margin-bottom:6px', text: 'Also compared with the chat message:' }),
      el('div', { class: 'chips' }, compared.map(t => el('span', { class: 'chip static mono', text: t })))) : null);
}

function describeSave(save) {
  if (!save) return 'nothing the script shows';
  if (typeof save === 'string') return save;
  const parts = [];
  if ((save.kinds || []).length) parts.push(save.kinds.join(', '));
  const files = save.files || {};
  if ((files.writes || []).length) parts.push('writes ' + files.writes.slice(0, 6).join(', '));
  if ((files.reads || []).length) parts.push('reads ' + files.reads.slice(0, 6).join(', '));
  if ((save.game_caches || []).length) parts.push('game cache ' + save.game_caches.slice(0, 4).join(', '));
  if ((save.commands || []).length) parts.push('commands ' + save.commands.slice(0, 6).join(', '));
  if (save.platform && Object.keys(save.platform).length) parts.push('platform: ' + Object.keys(save.platform).join(', '));
  return parts.length ? parts.join('; ') : 'nothing the script shows';
}

function imageSlot(which, name) {
  const img = state.imageData[which];
  const box = el('div', { class: 'preview', style: 'width:200px;height:200px;min-height:0' },
    img ? rgbaCanvas(img, 180) : el('span', { class: 'faint', text: name ? 'cannot show it' : 'none' }));
  const label = { minimap: 'Minimap', preview: 'Preview' }[which];
  return el('div', {}, el('div', { class: 'muted', text: label + (name ? ' (' + name + ')' : '') }), box,
    el('button', { class: 'btn small', style: 'margin-top:6px', text: 'Replace...', onclick: () => replaceImage(which,
      box) }));
}

async function replaceImage(which, box) {
  const p = await api().pick_file('image');
  if (!p) return;
  const b64 = await api().read_file(p);
  const ext = p.toLowerCase().split('.').pop();
  if (!['png', 'jpg', 'jpeg', 'bmp'].includes(ext)) { toast('Pick a PNG, JPG or BMP image.', { bad: true }); return; }
  const img = new Image();
  img.onload = () => {
    const size = which === 'minimap' ? 256 : Math.min(256, Math.max(img.width, img.height));
    const c = el('canvas', { width: size, height: size });
    const ctx = c.getContext('2d');
    ctx.drawImage(img, 0, 0, size, size);
    const data = ctx.getImageData(0, 0, size, size).data;
    let bin = '';
    for (let i = 0; i < data.length; i += 0x8000) bin += String.fromCharCode.apply(null, data.subarray(i, i + 0x8000));
    const ch = state.extras.card || {};
    ch.images = Object.assign({}, ch.images, { [which]: { width: size, height: size, rgba: btoa(bin) } });
    state.extras.card = ch;
    c.style.width = '180px';
    box.replaceChildren(c);
    renderActions();
  };
  img.onerror = () => toast('The image ' + base(p) + ' could not be read: pick a valid PNG, JPG or BMP under 32 MB.',
    { bad: true });
  img.src = 'data:image/' + (ext === 'jpg' ? 'jpeg' : ext) + ';base64,' + b64;
}

function renderReforged() {
  const base = state.reforged;
  if (!base) { tabBody('reforged', el('div', { class: 'card muted', text: 'Checking...' })); return; }
  const g = state.gameCheck;
  const older = g && g.version;
  if (older && !g.result) {
    tabBody('reforged', el('div', { class: 'card' }, gamePicker(base, older),
      g.error ? el('p', { class: 'muted' }, el('span', { text: 'Could not check:' }), ' ', el('span', { text: g.error }))
        : el('p', { class: 'muted', text: 'Checking...' })));
    return;
  }
  const r = older ? g.result : base;
  const sev = { blocker: 'bad', warning: 'warn', info: 'info' };
  const verdict = older ? ({ 'v-yes': 'Yes, it should run on this version.',
    'v-probably': 'Probably: nothing known stops it.', 'v-no': 'Not as it is: see the blockers below.',
    'v-unknown': 'Cannot tell.' }[r.verdict_code] || 'Cannot tell.') :
    ({ 'v-yes': 'Yes, it should run on Reforged.', 'v-probably': 'Probably: nothing known stops it.',
      'v-no': 'Not as it is: see the blockers below.', 'v-unknown': 'Cannot tell.' }[r.verdict_code] ||
      'Cannot tell.');
  const fix = { doctor: '"Fix map" or "Open in World Editor" takes care of it.', port: 'It needs a port, not a fix.',
    none: '' };
  const made = r.made_for || base.made_for;
  tabBody('reforged', el('div', { class: 'card' }, gamePicker(base, older), el('h2', { text: verdict }),
    el('p', { class: 'lead', text: older ? 'A "yes" means none of the known limits of that version is there.' :
      'A "yes" means none of the measured problems is there.' }),
    made && made.label ? el('p', { class: 'muted' }, el('span', { text: 'Made for:' }), ' ',
      el('b', { text: made.label }), el('span', { class: 'faint', text: ' (' + (made.reasons || []).join('; ') + ')' }))
      : null,
    (r.items || []).length ? el('div', { class: 'report' }, r.items.map(it => el('div', { class: 'step' },
      el('span', { class: 'badge ' + (sev[it.severity] || ''), text: it.severity }),
      el('div', {}, el('div', { text: it.text }), fix[it.fix] ? el('div', { class: 'd muted', text: fix[it.fix] }) :
        null)))) : el('p', { class: 'muted', text: 'Nothing found.' })),
    older ? downgradeCard(older) : null);
}

function downgradeCard(version) {
  const g = state.gameCheck || {};
  return el('div', { class: 'card' },
    el('h2', { text: 'Take the map info to this version' }),
    el('p', { class: 'muted', text: 'Writes war3map.w3i in the format this game reads (flags it does not know cleared). ' +
      'Only the map info: the object data, the triggers and the terrain stay as they are, and the report lists them.' }),
    el('div', { class: 'foot' }, el('button', { class: 'btn needs-idle', text: 'Write the older map info',
      disabled: !!state.running, onclick: async () => {
        try {
          g.downgrade = await run('downgrade_w3i', { version }, { label: 'Writing the map info...' });
        } catch (e) { failed(e, 'Writing the map info'); return; }
        renderReforged();
      } })),
    g.downgrade ? el('div', {}, reportLines(g.downgrade.lines || []),
      g.downgrade.file ? el('div', { class: 'foot row' }, el('span', { class: 'faint mono grow', text: g.downgrade.file }),
        folderButton(g.downgrade.file)) : null) : null);
}

function gamePicker(base, current) {
  const list = base.versions || [{ value: '', label: 'Reforged (3.0)' }];
  if (list.length < 2) return null;
  return el('div', { class: 'row' }, el('span', { class: 'muted', text: 'Check against:' }),
    el('select', { class: 'field', style: 'width:auto', title: 'The game version to check the map against',
      onchange: e => checkGameVersion(e.target.value) },
    ...list.map(x => el('option', { value: x.value, text: x.label, selected: (x.value || '') === (current || '') }))));
}

async function checkGameVersion(version) {
  const gen = state.gen;
  if (!version) { state.gameCheck = null; renderReforged(); return; }
  state.gameCheck = { version, result: null };
  renderReforged();
  try {
    const r = await run('reforged', { version }, { quiet: true });
    if (gen !== state.gen || !state.gameCheck || state.gameCheck.version !== version) return;
    state.gameCheck.result = r;
  } catch (e) {
    if (gen !== state.gen || !state.gameCheck || state.gameCheck.version !== version) return;
    state.gameCheck.error = String(e && e.message || e);
  }
  renderReforged();
}

async function loadFiles(gen) {
  try {
    const f = await run('files', {}, { quiet: true });
    if (gen !== state.gen) return;
    state.files = f;
    renderFiles();
    setTabState('files', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('files', 'Listing the files', e); }
}

function renderFiles() {
  const f = state.files;
  const all = f.files.map(x => ({ id: x.name, label: x.name, kind: x.kind, size: x.size, about: x.about || '',
    file: x, named: true })).concat((f.unnamed || []).map(x => {
    const id = x.name || '#' + x.block;
    return { id, label: x.path || id, kind: x.kind, size: x.size, about: 'No name: block ' + x.block +
      ', the kind found by its content', file: Object.assign({}, x, { name: id }), named: false };
  }));
  const models = all.filter(x => x.kind === 'model').length;
  const filter = el('input', { class: 'field', type: 'text', placeholder: 'Filter by name or kind',
    style: 'max-width:320px' });
  const rows = el('tbody');
  const preview = el('div', { class: 'preview' }, el('span', { class: 'faint', text: 'Click a file to see it.' }));
  const selected = new Set();
  const shown = () => {
    const q = filter.value.toLowerCase();
    return all.filter(x => !q || x.label.toLowerCase().includes(q) || x.kind.includes(q));
  };
  const allBox = el('input', { type: 'checkbox', title: 'Select all the files the filter shows', onclick: e => {
    for (const x of shown()) { if (e.target.checked) selected.add(x.id); else selected.delete(x.id); }
    draw();
  } });
  const syncAll = list => {
    const n = list.filter(x => selected.has(x.id)).length;
    allBox.checked = !!list.length && n === list.length;
    allBox.indeterminate = n > 0 && n < list.length;
  };
  const draw = () => {
    const list = shown();
    rows.replaceChildren(...list.slice(0, 3000).map(x => {
      const box = el('input', { type: 'checkbox', checked: selected.has(x.id), onclick: e => { e.stopPropagation();
        if (e.target.checked) selected.add(x.id); else selected.delete(x.id); syncAll(list); } });
      const tr = el('tr', { class: 'click', onclick: () => {
        $$('tr.sel', rows).forEach(r => r.classList.remove('sel')); tr.classList.add('sel'); showPreview(x.file, preview);
      } }, el('td', {}, box), el('td', { class: 'mono' + (x.named ? '' : ' faint'), text: x.label, title: x.about },
        ...(x.named ? lintBadges(x.id) : [])), el('td', { text: x.kind }),
      el('td', { style: 'text-align:right', text: (x.size / 1024).toFixed(x.size < 10240 ? 1 : 0) + ' KB' }));
      return tr;
    }));
    syncAll(list);
  };
  filter.addEventListener('input', draw);
  draw();
  const pkg = !!(state.open && state.open.summary.package);
  tabBody('files', pkg ? null : rawcodesCard(), pkg ? null : recipesCard(), el('div', { class: 'card' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: f.files.length + ' files' +
      (f.unnamed && f.unnamed.length ? ', ' + f.unnamed.length + ' without a name' : '') }), filter,
      el('button', { class: 'btn needs-idle', text: 'Extract selected...', disabled: !!state.running,
        onclick: () => {
          if (!selected.size) { toast('Tick the files to extract first.'); return; }
          extractFiles('extract', { names: Array.from(selected) });
        } }),
      el('button', { class: 'btn needs-idle', text: 'Extract all...', disabled: !!state.running || !all.length,
        'data-off': !all.length, title: 'Every file, at its path; the ones without a name in a folder named unnamed',
        onclick: () => extractFiles('extract_all', {}) }),
      el('button', { class: 'btn needs-idle', text: 'Extract models...', disabled: !!state.running || !models,
        'data-off': !models, title: 'Every model with the textures and emitter models it needs, at the paths the ' +
          'models cite, so a model viewer opens them',
        onclick: () => extractFiles('extract_all', { kind: 'models' }) })),
    f.error ? el('div', { class: 'report' }, el('div', { class: 'l bad', text: f.error })) : null,
    (f.notes || []).map(n => el('p', { class: 'muted', text: n })),
    lintSummary(f),
    el('div', { class: 'split', style: 'margin-top:12px' },
      el('div', { class: 'scroll' }, el('table', { class: 'grid' }, el('thead', {}, el('tr', {}, el('th', {}, allBox),
        el('th', { text: 'Name' }), el('th', { text: 'Kind' }), el('th', { text: 'Size', style: 'text-align:right' }))),
      rows)), preview)));
}

async function extractFiles(task, params) {
  if (state.running) return;
  const dir = await api().pick_folder();
  if (!dir) return;
  const label = task === 'extract' ? 'Extracting...' : params.kind === 'models' ? 'Extracting the models...' :
    'Extracting every file...';
  try {
    const r = await run(task, Object.assign({ folder: dir }, params), { label });
    if (r.error) { failed({ message: r.error }, 'Extracting'); return; }
    const n = (r.written || []).length, bad = r.failed || [], kept = (r.exists || []).length,
      same = (r.same || []).length;
    if (bad.length) toast(bad.length + (bad.length === 1 ? ' file' : ' files') + ' could not be extracted: ' +
      bad.slice(0, 5).map(x => x.name + (x.reason ? ' (' + x.reason + ')' : '')).join(', ') +
      (bad.length > 5 ? ', ...' : ''), { bad: true, sticky: true });
    const show = { actions: [[showLabel('Show'), () => api().open_folder(dir)]] };
    if (params.kind === 'models') {
      const out = (r.outside || []).length;
      toast('Extracted ' + r.models + (r.models === 1 ? ' model' : ' models') + ' with ' + r.textures +
        (r.textures === 1 ? ' texture or emitter model' : ' textures and emitter models') +
        (same ? ', ' + same + ' already there' : '') + '.', show);
      if (out) toast(out + (out === 1 ? ' file the models use is' : ' files the models use are') +
        ' not in this file: the game has them, or they are missing.', { ms: 9000 });
    } else {
      toast('Extracted ' + n + (n === 1 ? ' file' : ' files') + (same ? ', ' + same + ' already there' : '') +
        (kept ? ', ' + kept + ' left as they were' : '') + '.', show);
    }
  } catch (e) { failed(e, 'Extracting'); }
}

const LINT_TEXT = {
  not_in_imp: ['not in the import list', 'The World Editor drops it on the next save.'],
  odd_extension: ['not a game file', 'The game does not load this type of file.'],
  game_file: ['replaces a game file', 'The game shows this file instead of its own.'],
};

function lintBadges(name) {
  const codes = ((state.files || {}).lint || {})[name] || [];
  return codes.map(c => el('span', { class: 'badge' + (c === 'game_file' ? '' : ' warn'), style: 'margin-left:6px',
    text: (LINT_TEXT[c] || [c])[0], title: (LINT_TEXT[c] || ['', ''])[1] }));
}

function lintSummary(f) {
  const c = f.lint_counts || {};
  const parts = Object.keys(LINT_TEXT).filter(k => c[k]).map(k => c[k] + ' ' + LINT_TEXT[k][0]);
  return parts.length ? el('p', { class: 'lead', text: 'Imported files: ' + parts.join(', ') + '.' }) : null;
}

const MODEL3D_TEXT = ['The 3D preview needs WebGL, and this browser has none.', 'This model cannot be shown in 3D',
  'This model has no geometry to show.', 'The 3D preview could not start', 'The 3D preview stopped',
  'The 3D preview lost its WebGL context.'];
function model3dButton(file, box, seq) {
  const stage = el('div', {});
  const btn = el('button', { class: 'btn', text: '3D preview', onclick: async () => {
    btn.disabled = true;
    stage.replaceChildren(el('span', { class: 'faint', text: 'Loading...' }));
    try {
      const m = await run('model3d', { name: file.name }, { quiet: true });
      if (box.previewSeq !== seq) return;
      if (m.error || !m.drawable) {
        stage.replaceChildren(el('span', { class: 'faint', text: m.error || (m.version ? 'This model is version ' +
          m.version + '; the 3D preview draws versions 800 to 1100.' : m.reason || 'This model cannot be shown in 3D') }));
        btn.disabled = false;
        return;
      }
      const canvas = el('canvas', { style: 'width:100%;max-width:520px;height:380px;display:block;background:#222;' +
        'touch-action:none' });
      stage.replaceChildren(canvas);
      window.Model3D.t = s => (window.doctorI18n ? window.doctorI18n.tr(s) : s);
      await window.Model3D.show(canvas, m.model, m.textures);
      if ((m.outside || []).length) stage.append(el('p', { class: 'faint', text: m.outside.length +
        ' textures only the game has are not drawn.' }));
    } catch (e) {
      stage.replaceChildren(el('span', { class: 'bad', text: (e && e.message) || String(e) }));
    }
    btn.disabled = false;
  } });
  return el('div', { style: 'width:100%' }, btn, stage);
}
void MODEL3D_TEXT;

async function showPreview(file, box) {
  const seq = box.previewSeq = (box.previewSeq || 0) + 1;
  box.replaceChildren(el('span', { class: 'faint', text: 'Loading...' }));
  try {
    const p = await run('preview', { name: file.name }, { quiet: true });
    if (box.previewSeq !== seq) return;
    if (p.error) box.replaceChildren(el('span', { class: 'bad', text: 'Cannot show it: ' + p.error }));
    else if (p.kind === 'image' && p.rgba) box.replaceChildren(rgbaCanvas(p, 420));
    else if (p.kind === 'image' && p.data) box.replaceChildren(el('img', { src: 'data:' + p.mime + ';base64,' + p.data }));
    else if (p.kind === 'sound') box.replaceChildren(el('audio', { controls: true, src: 'data:' + p.mime + ';base64,' +
      p.data }));
    else if (p.kind === 'text' || p.kind === 'script') box.replaceChildren(el('pre', { class: 'code', style: 'width:100%',
      text: p.text + (p.truncated ? '\n\n(cut short)' : '') }));
    else if (p.kind === 'model') box.replaceChildren(el('pre', { class: 'code', style: 'width:100%',
      text: JSON.stringify(p.info, null, 1) }), model3dButton(file, box, seq));
    else box.replaceChildren(el('pre', { class: 'code', style: 'width:100%', text: p.hex || '(empty)' }));
  } catch (e) {
    if (box.previewSeq !== seq) return;
    box.replaceChildren(el('span', { class: 'bad', text: 'Cannot show it: ' + (e.message || e) }));
  }
}

function rawcodesCard() {
  const body = el('div', {});
  if (state.rawcodes) drawRawcodes(body, state.rawcodes);
  const btn = el('button', { class: 'btn', text: 'Read the raw codes', onclick: async () => {
    if (state.running) return;
    btn.disabled = true;
    body.replaceChildren(el('span', { class: 'faint', text: 'Reading the raw codes...' }));
    try {
      const r = await run('rawcodes', {}, { quiet: true });
      state.rawcodes = r;
      drawRawcodes(body, r);
    } catch (e) {
      body.replaceChildren(el('div', { class: 'report' },
        el('div', { class: 'l bad', text: 'Reading the raw codes failed.' }),
        el('div', { class: 'l info', text: (e && e.message) || String(e) })));
    }
    btn.disabled = false;
  } });
  return el('div', { class: 'card' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'Raw codes' }), btn),
    el('p', { class: 'lead', text: 'Every object id in the map, with its name.' }),
    body);
}

function nonAsciiIds(text, kinds) {
  const ids = new Set();
  (kinds || []).forEach(k => (k.ids || []).forEach(i => ids.add(i)));
  let n = 0;
  for (const id of ids) {
    for (let i = 0; i < id.length; i++) {
      const c = id.charCodeAt(i);
      if (c < 0x20 || c > 0x7e) { n += 1; break; }
    }
  }
  if (ids.size) return n;
  return (kinds || []).reduce((a, k) => a + (k.ansii || 0), 0);
}

function visibleId(id) {
  let out = '';
  for (const ch of id) {
    const c = ch.codePointAt(0);
    if (c >= 0xDC80 && c <= 0xDCFF) out += '\\x' + (c - 0xDC00).toString(16).padStart(2, '0');
    else if (c < 0x20 || c === 0x7f) out += '\\x' + c.toString(16).padStart(2, '0');
    else out += ch;
  }
  return out;
}

const RAW_LIMIT = 1500;
function drawRawcodes(body, r) {
  if (r.error) {
    body.replaceChildren(el('div', { class: 'report' }, el('div', { class: 'l bad', text: r.error })));
    return;
  }
  const kinds = r.kinds || [];
  const names = r.names || {};
  const rows = [], seen = new Set(), perKind = {};
  for (const k of kinds) {
    for (const id of k.ids || []) {
      if (seen.has(id)) continue;
      seen.add(id);
      const shown = visibleId(id);
      rows.push({ id, shown, odd: shown !== id, name: names[id] || '', kind: k.kind, source: k.source });
      perKind[k.kind] = (perKind[k.kind] || 0) + 1;
    }
  }
  const total = r.total === undefined || r.total === null ? rows.length : r.total;
  const ansii = nonAsciiIds(r.text, kinds);
  const named = rows.filter(x => x.name).length;
  const view = { kind: null, q: '' };
  const tbody = el('tbody', {});
  const count = el('span', { class: 'faint' });
  const chips = el('div', { class: 'chips' });
  const draw = () => {
    const q = view.q.toLowerCase();
    const hit = rows.filter(x => (!view.kind || x.kind === view.kind) &&
      (!q || x.shown.toLowerCase().includes(q) || x.name.toLowerCase().includes(q)));
    tbody.replaceChildren(...hit.slice(0, RAW_LIMIT).map(x => el('tr', {},
      el('td', { class: 'mono rc-id' + (x.odd ? ' warn' : ''), text: x.shown }),
      el('td', { class: x.name ? '' : 'faint', text: x.name || '-' }),
      el('td', { class: 'mono muted', text: x.kind }),
      el('td', { class: 'mono faint', text: x.source }))));
    count.textContent = hit.length > RAW_LIMIT ? 'showing ' + RAW_LIMIT + ' of ' + hit.length :
      hit.length + (hit.length === 1 ? ' code' : ' codes');
    chips.replaceChildren(...[[null, 'all', rows.length]].concat(Object.entries(perKind).map(([k, n]) => [k, k, n]))
      .map(([k, label, n]) => el('button', { class: 'chip' + (view.kind === k ? ' on' : ''), onclick: () => {
        view.kind = k; draw(); } }, label, el('span', { class: 'n', text: String(n) }))));
  };
  const search = el('input', { class: 'field', type: 'search', placeholder: 'Search an id or a name',
    oninput: e => { view.q = e.target.value.trim(); draw(); } });
  draw();
  body.replaceChildren(
    el('div', { class: 'rc-stats' },
      el('span', {}, el('b', { text: String(total) }), ' raw codes'),
      el('span', {}, el('b', { text: String(named) }), ' with a name'),
      el('span', { class: ansii ? 'warn' : '' }, el('b', { text: String(ansii) }), ' not ASCII (the PG family)')),
    rows.length ? el('div', {}, chips,
      el('div', { class: 'row rc-tools' }, search, count),
      el('div', { class: 'scroll', style: 'max-height:440px' }, el('table', { class: 'grid rc' },
        el('thead', {}, el('tr', {}, el('th', { text: 'Id' }), el('th', { text: 'Name' }), el('th', { text: 'Kind' }),
          el('th', { text: 'Source' }))), tbody))) :
      el('p', { class: 'muted', text: 'No object data to read in this map.' }),
    r.note ? el('p', { class: 'faint', style: 'margin:8px 0 0', text: r.note }) : null,
    kinds.length ? el('details', { class: 'rc-about' }, el('summary', { text: 'Sources' }),
      el('table', { class: 'grid', style: 'margin:8px 0' },
        el('thead', {}, el('tr', {}, el('th', { text: 'Source' }), el('th', { text: 'Kind' }),
          el('th', { text: 'Codes' }), el('th', { text: 'Not ASCII' }))),
        el('tbody', {}, kinds.map(k => el('tr', {}, el('td', { class: 'mono', text: k.source }),
          el('td', { class: 'muted', text: k.kind }),
          el('td', { text: String(k.count === undefined || k.count === null ? (k.ids || []).length : k.count) }),
          el('td', { class: k.ansii ? 'warn' : 'faint', text: String(k.ansii || 0) })))))) : null,
    r.text ? el('div', { class: 'row', style: 'margin-top:12px' },
      el('button', { class: 'btn', text: 'Copy all', onclick: async () => {
        await copyText(r.text);
        toast('The raw codes are in the clipboard.');
      } }),
      el('button', { class: 'btn', text: 'Save as...', onclick: async () => {
        const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + '_rawcodes.txt', 'text');
        if (p) { await api().write_text(p, r.text); toast('Saved ' + base(p) + '.'); }
      } }),
      el('span', { class: 'faint', text: 'One per line: kind, id, name.' })) : null);
}

const RECIPE_LIMIT = 1500;
function recipesCard() {
  const body = el('div', {});
  if (state.recipes) drawRecipes(body, state.recipes);
  const btn = el('button', { class: 'btn', text: 'Find recipes', onclick: async () => {
    if (state.running) return;
    btn.disabled = true;
    body.replaceChildren(el('span', { class: 'faint', text: 'Looking for recipes...' }));
    try {
      const r = await run('recipes', {}, { quiet: true });
      state.recipes = r;
      drawRecipes(body, r);
    } catch (e) {
      body.replaceChildren(el('div', { class: 'report' },
        el('div', { class: 'l bad', text: 'Finding the recipes failed.' }),
        el('div', { class: 'l info', text: (e && e.message) || String(e) })));
    }
    btn.disabled = false;
  } });
  return el('div', { class: 'card' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'Item recipes' }), btn),
    el('p', { class: 'lead', text: 'The items the map script combines into another item, with their ids and names.' }),
    body);
}

function drawRecipes(body, r) {
  if (r.error) {
    body.replaceChildren(el('div', { class: 'report' }, el('div', { class: 'l bad', text: r.error })));
    return;
  }
  const list = r.recipes || [];
  const tbody = el('tbody', {});
  const count = el('span', { class: 'faint' });
  const view = { q: '' };
  const draw = () => {
    const q = view.q.toLowerCase();
    const hit = list.filter(x => !q || (x.line || '').toLowerCase().includes(q));
    tbody.replaceChildren(...hit.slice(0, RECIPE_LIMIT).map(x => el('tr', {},
      el('td', { text: x.line || '' }),
      el('td', { class: 'faint', text: x.where || '' }))));
    count.textContent = hit.length > RECIPE_LIMIT ? 'showing ' + RECIPE_LIMIT + ' of ' + hit.length :
      hit.length + (hit.length === 1 ? ' recipe' : ' recipes');
  };
  const search = el('input', { class: 'field', type: 'search', placeholder: 'Search an id or a name',
    oninput: e => { view.q = e.target.value.trim(); draw(); } });
  draw();
  body.replaceChildren(
    list.length ? el('div', {},
      el('div', { class: 'row rc-tools' }, search, count),
      el('div', { class: 'scroll', style: 'max-height:440px' }, el('table', { class: 'grid' },
        el('thead', {}, el('tr', {}, el('th', { text: 'Recipe' }), el('th', { text: 'Where' }))), tbody))) :
      el('p', { class: 'muted', text: 'No recipe found in the script.' }),
    r.note ? el('p', { class: 'faint', style: 'margin:8px 0 0', text: r.note }) : null,
    list.length ? el('div', { class: 'row', style: 'margin-top:12px' },
      el('button', { class: 'btn', text: 'Copy all', onclick: async () => {
        await copyText(r.text);
        toast('The recipes are in the clipboard.');
      } }),
      el('button', { class: 'btn', text: 'Save as...', onclick: async () => {
        const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + '_recipes.txt', 'recipes');
        if (!p) return;
        const ext = p.toLowerCase().split('.').pop();
        await api().write_text(p, ext === 'json' ? r.json : ext === 'csv' ? r.csv : r.text);
        toast('Saved ' + base(p) + '.');
      } }),
      el('span', { class: 'faint', text: 'A .txt file has one recipe per line; .json and .csv keep every field.' })) :
      null);
}

async function loadScript(gen) {
  try {
    const s = await run('script', {}, { quiet: true });
    if (gen !== state.gen) return;
    const shown = s.text && s.text.length > 3e6 ? s.text.slice(0, 3e6) + '\n\n(shown up to 3 MB; the export has it all)' :
      s.text;
    tabBody('script', el('div', { class: 'card' },
      el('div', { class: 'row' }, el('h2', { class: 'grow', text: (s.name || 'Script') + (s.size ? ' (' + mb(s.size) +
        ')' : '') }),
      s.text ? el('button', { class: 'btn', text: 'Export...', onclick: async () => {
        const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + (s.language === 'lua' ? '.lua' : '.j'),
          'script');
        if (p) { await api().write_text(p, s.text); toast('Saved ' + base(p) + '.'); }
      } }) : null),
      s.note ? el('p', { class: 'lead', text: s.note }) : null,
      s.language === 'jass' && s.text ? scriptChecksCard() : null,
      s.text ? el('pre', { class: 'code', text: shown }) :
        s.error ? el('div', { class: 'report' }, el('div', { class: 'l bad', text: s.error })) :
          el('p', { class: 'muted', text: 'No readable script.' })));
    setTabState('script', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('script', 'Reading the script', e); }
}

const HEAT_TEXT = { hot: 'periodic timer', repeat: 'event', once: 'start', unused: 'never runs' };
const RULE_TEXT = { discarded: 'created and thrown away', inline: 'created inside a call, never destroyed',
  never_destroyed: 'kept in a local, never destroyed' };

function scriptChecksCard() {
  const box = el('div', { class: 'muted', text: 'Handle leaks, start-up functions nothing calls, globals ' +
    'read and never set.' });
  const btn = el('button', { class: 'btn', text: 'Script checks', onclick: async () => {
    btn.disabled = true;
    box.replaceChildren(el('span', { class: 'faint', text: 'Checking...' }));
    try {
      const r = await run('script_checks', {}, { quiet: true });
      const kids = (r.lines || []).map((l, i) => el(i ? 'div' : 'p', { class: i ? 'mono' : 'lead', text: l }));
      if (r.leaks && r.leaks.length) {
        const rows = r.leaks.slice(0, 200).map(x => el('tr', {}, el('td', { class: 'mono', text: String(x.line) }),
          el('td', { class: 'mono', text: x['function'] }), el('td', { text: x.creator }),
          el('td', { text: RULE_TEXT[x.rule] || x.rule }), el('td', { text: HEAT_TEXT[x.heat] || x.heat })));
        kids.push(el('div', { class: 'scroll', style: 'max-height:260px;margin-top:8px' }, el('table', { class: 'grid' },
          el('thead', {}, el('tr', {}, el('th', { text: 'Line' }), el('th', { text: 'Function' }),
            el('th', { text: 'Creates' }), el('th', { text: 'Leak' }), el('th', { text: 'Runs on' }))),
          el('tbody', {}, ...rows))));
      }
      box.replaceChildren(...kids);
    } catch (e) { box.replaceChildren(el('span', { class: 'bad', text: 'The checks failed: ' + (e.message || e) })); }
    btn.disabled = false;
  } });
  return el('div', { class: 'card', style: 'margin:10px 0' }, el('div', { class: 'row' },
    el('h3', { class: 'grow', text: 'Script checks' }), btn), box);
}

async function loadCheatpacks(gen) {
  try {
    const s = await run('cheatpacks', {}, { quiet: true });
    if (gen !== state.gen) return;
    if (s.error) { tabFailed('cheatpacks', 'Reading the cheat packs', { message: s.error }); return; }
    state.cheatpacks = s;
    const packs = s.packs || [];
    if (!packs.some(p => p.id === state.cheatPack.id)) state.cheatPack.id = packs.length ? packs[0].id : null;
    renderCheatpacks();
    setTabState('cheatpacks', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('cheatpacks', 'Reading the cheat packs', e); }
}

function renderCheatpacks() {
  const d = state.cheatpacks;
  if (!d) return;
  const packs = d.packs || [];
  const head = el('div', { class: 'card' },
    el('h2', { text: 'Cheat packs' }),
    el('p', { class: 'lead', text: 'Puts one cheat pack into the map\'s script, obfuscated, with the ' +
      'options below. Saves an edited copy.' }),
    el('div', { class: 'badges' },
      el('span', { class: 'badge ' + (d.language ? 'info' : 'warn'), text: d.language ?
        'The map script is ' + (d.language === 'lua' ? 'Lua' : 'JASS') : 'The map script cannot be written' }),
      d.script ? el('span', { class: 'badge', text: d.script + (d.size ? ' (' + mb(d.size) + ')' : '') }) : null),
    packs.length ? el('p', { class: 'muted', text: packs.length +
      (packs.length === 1 ? ' pack fits' : ' packs fit') + ' this map: pick one and inject it.' }) :
      el('p', { class: 'muted', text: d.why || 'The map script is not one the Doctor can write.' }),
    d.note ? el('p', { class: 'faint', text: d.note }) : null);
  tabBody('cheatpacks', head, cheatpackFound(d), packs.map(cheatpackCard),
    state.cheatPack.result ? cheatpackResult(state.cheatPack.result) : null);
}

function cheatpackFound(d) {
  const found = d.found || [];
  return el('div', { class: 'card', id: 'cheatpacks-found' },
    el('h2', { text: 'Cheat packs already in this map' }),
    found.length ? el('p', { class: 'lead', text: found.length +
      (found.length === 1 ? ' cheat pack' : ' cheat packs') + ' in the map\'s own script.' }) : null,
    found.length ? el('ul', { class: 'steps' }, found.map(cheatpackFoundItem)) :
      el('p', { class: 'muted', text: 'No cheat pack found in this map\'s script.' }));
}

function cheatpackFoundItem(f) {
  return el('li', { class: 'step' }, el('div', { class: 'grow' },
    el('div', { class: 'row' }, el('span', { class: 'grow t', text: f.title || f.id }),
      el('span', { class: 'badge ' + (f.confidence === 'low' ? 'warn' : 'good'),
        text: f.confidence === 'low' ? 'guess' : 'certain' })),
    f.activator ? el('div', { style: 'margin-top:2px' }, el('span', { class: 'mono badge', text: f.activator })) : null,
    el('div', { class: 'faint', text: [f.where, f.evidence].filter(Boolean).join('  -  ') })));
}

function cheatpackCard(p) {
  const chosen = p.id === state.cheatPack.id;
  const radio = el('input', { type: 'radio', name: 'cheatpack', checked: chosen, title: 'Inject this one',
    'aria-label': 'Choose ' + p.title, onchange: () => { state.cheatPack.id = p.id; renderCheatpacks(); } });
  return el('div', { class: 'card', id: 'cheatpack-' + p.id },
    el('div', { class: 'row' }, radio, el('h2', { class: 'grow', text: p.title }),
      el('span', { class: 'badge', text: p.language === 'lua' ? 'Lua' : 'JASS' })),
    p.file ? el('div', { class: 'faint mono', text: p.file }) : null,
    p.needs ? el('div', { class: 'muted', style: 'margin-top:4px', text: 'Works on: ' + p.needs }) : null,
    chosen ? el('div', { class: 'form', style: 'margin-top:12px' }, (p.options || []).map(cheatpackField).flat(),
      el('ul', { class: 'steps', style: 'grid-column:1 / -1' }, stripIndentItem(),
        optionItem({ checked: state.cheatDurable === true,
          title: 'Also keep a readable copy in the map\'s triggers',
          detail: 'So the pack can survive a save in the World Editor; a call to it goes in the first custom text ' +
            'trigger. The copy is readable, not obfuscated. Not tried in the editor.',
          onchange: e => { state.cheatDurable = e.target.checked; } })),
      el('div', { style: 'grid-column:1 / -1' }, el('button', { class: 'btn primary needs-idle',
        text: 'Inject the cheat pack', disabled: !!state.running, onclick: runCheatpack }))) : null);
}

function cheatpackField(o) {
  const v = state.cheatPack.options[o.key];
  const value = v === undefined ? o.default : v;
  if (o.kind === 'bool') {
    return [el('ul', { class: 'steps', style: 'grid-column:1 / -1' }, optionItem({
      checked: String(value).toLowerCase() === 'true', title: o.label, detail: o.note, onchange: e => {
        state.cheatPack.options[o.key] = e.target.checked ? 'true' : 'false'; } }))];
  }
  return [el('label', { text: o.label }),
    el('input', { class: 'field', type: 'text', value: value === null || value === undefined ? '' : String(value),
      oninput: e => { state.cheatPack.options[o.key] = e.target.value; } })];
}

function cheatpackOptions() {
  const p = ((state.cheatpacks || {}).packs || []).find(x => x.id === state.cheatPack.id);
  const out = {};
  ((p && p.options) || []).forEach(o => {
    const v = state.cheatPack.options[o.key];
    out[o.key] = v === undefined ? o.default : v;
  });
  return out;
}

async function runCheatpack() {
  if (state.running) return;
  const pack = state.cheatPack.id;
  if (!pack) { toast('Pick a cheat pack first.'); return; }
  status('Injecting the cheat pack...');
  try {
    const r = await run('cheatpack_inject', { pack, options: cheatpackOptions(), strip_indent: stripIndentOn(),
      durable: state.cheatDurable === true },
      { label: 'Injecting the cheat pack...' });
    state.cheatPack.result = r;
    state.results.cheatpacks = r;
    renderCheatpacks();
    status(r.outcome === 'ok' ? 'Cheat pack injected.' : 'The injection stopped.');
    if (r.outcome !== 'ok') toast('The cheat pack was not injected.', { bad: true });
  } catch (e) {
    failed(e, 'Injecting the cheat pack');
    if (e && e.cancelled) { renderCheatpacks(); return; }
    const msg = (e && e.message) || String(e);
    const lines = [['bad', 'The injection stopped: ' + msg]];
    if (e && e.trace) e.trace.split('\n').filter(l => l.trim()).forEach(l => lines.push(['info', '  ' + l]));
    state.cheatPack.result = { outcome: 'failed', lines, pack, file: null };
    renderCheatpacks();
  }
}

function cheatpackResult(r) {
  const ok = r.outcome === 'ok';
  return el('div', { class: 'card' + (ok ? '' : ' bad'), id: 'result-cheatpacks' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'Cheat pack: result' }),
      el('span', { class: 'badge ' + (ok ? 'good' : 'bad'), text: ok ? 'Injected' : 'Stopped' })),
    ok ? null : el('div', { class: 'report' }, el('div', { class: 'l bad',
      text: 'The cheat pack was not injected.' })),
    reportLines(r.lines || []),
    el('div', { class: 'foot row', style: 'margin-top:14px' },
      r.file ? el('span', { class: 'faint mono grow', text: r.file }) : null,
      r.file ? folderButton(r.file) : null,
      ok ? null : el('button', { class: 'btn ghost', text: 'Report a problem', onclick: reportProblem })));
}

const QOL_NUMBERS = [
  ['xp', 'Experience', 'Multiplies the experience: kills and what the triggers give.'],
  ['gold', 'Gold', 'Multiplies every gold gain: kills, triggers, mining, selling.'],
  ['lumber', 'Lumber', 'Multiplies every lumber gain.'],
  ['drop', 'Item drop chance', 'Multiplies the chance of the item drops the script rolls (100% at most).'],
  ['craft', 'Craft success chance', 'Multiplies the chance of the crafts the script rolls (100% at most).'],
  ['respawn', 'Hero revive time', 'Multiplies the time a dead hero waits: 0.5 is half the time, 0 is at once.'],
  ['creep', 'Monster respawn time', 'Multiplies the time a dead monster takes to come back: 0.5 is half the time.'],
];
const QOL_FLAGS = { xp: 'xp', gold: 'gold', lumber: 'lumber', drop: 'drop', craft: 'craft', respawn: 'respawn',
  creep: 'creep',
  noshake: 'noshake', noshake_default: 'noshake-off', reveal: 'reveal', vip: 'vip' };

async function loadQol(gen) {
  try {
    const s = await run('qol', {}, { quiet: true });
    if (gen !== state.gen) return;
    if (s.error) { tabFailed('qol', 'Reading the map for the QoL edits', { message: s.error }); return; }
    state.qol = s;
    renderQol();
    setTabState('qol', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('qol', 'Reading the map for the QoL edits', e); }
}

function qolValue(key) {
  const v = state.qolOpt[key];
  return v === undefined ? ((state.qol || {}).defaults || {})[key] : v;
}

function qolOptions() {
  const out = {};
  const d = (state.qol || {}).defaults || {};
  for (const k of Object.keys(QOL_FLAGS)) {
    const v = qolValue(k);
    if (typeof d[k] === 'boolean') { if (v === true) out[k] = true; } else if (v !== undefined && v !== '' &&
      Number(v) !== Number(d[k]) && !isNaN(Number(v))) out[k] = Number(v);
  }
  return out;
}

function qolShell() {
  const cmd = $('#qol-shell .cmd');
  if (!cmd) return;
  const o = qolOptions();
  const name = state.open ? state.open.name : base(state.map);
  cmd.textContent = 'doctor qol "' + name + '"' + Object.keys(o).map(k => ' --' + QOL_FLAGS[k] +
    (o[k] === true ? '' : '=' + o[k])).join('') + (stripIndentOn() ? ' --strip-indent' : '');
}

function qolHint(key, f) {
  if (key === 'xp') {
    return f.xp_calls + ' call(s) of the map give experience or set its rate.' +
      (f.xp_set ? ' ' + f.xp_set + ' set a hero\'s experience or level directly: those stay as they are.' : '');
  }
  if (key === 'gold' && f.save_load) return 'The map has a save/load code: what a load gives back counts as a gain.';
  if (key === 'drop') {
    if (!f.drop_tables) return f.drop_chances + ' item drop roll(s) found.';
    return f.drop_chances + ' item drop roll(s) found. ' + f.drop_tables +
      ' item(s) in the item tables of the World Editor.';
  }
  if (key === 'craft') return f.craft_chances + ' craft roll(s) found.';
  if (key === 'creep') return f.creep_waits + ' wait(s) or timer(s) of a monster respawn found.';
  if (key === 'respawn') {
    return f.revive_waits + ' wait(s) or timer(s) of a hero revive found, in ' + f.revive_functions +
      ' function(s) that revive.';
  }
  return null;
}

function renderQol() {
  const d = state.qol;
  if (!d) return;
  const f = d.found || {};
  const head = el('div', { class: 'card' },
    el('h2', { text: 'Quality of life' }),
    el('p', { class: 'lead', text: 'Makes the map easier to play: more experience, gold and drops, a faster hero ' +
      'revive, no camera shakes. Saves an edited copy.' }),
    el('div', { class: 'badges' },
      el('span', { class: 'badge ' + (d.supported ? 'info' : 'warn'), text: !d.supported ?
        'The map cannot take the QoL edits' : d.language === 'lua' ? 'The map script is Lua' :
        'The map script is JASS' }),
      d.script ? el('span', { class: 'badge', text: d.script }) : null),
    d.supported ? null : el('p', { class: 'muted', text: d.reason || 'The map script is not one the Doctor can edit.' }),
    f.kk_mall || (d.reason || '').indexOf('KK') >= 0 ? el('p', { class: 'faint', text: 'Port to Reforged already ' +
      'unlocks the KK mall items, the map level and the VIP of the platform for every player.' }) : null);
  if (!d.supported) { tabBody('qol', head, state.qolResult ? qolResult(state.qolResult) : null); return; }
  const rows = [];
  for (const [key, label, detail] of QOL_NUMBERS) {
    const hint = qolHint(key, f);
    rows.push(el('label', { text: label }), el('div', {},
      el('div', { class: 'row' }, el('span', { class: 'mono', text: 'x' }), el('input', { class: 'field', type: 'number',
        min: '0', step: key === 'respawn' || key === 'creep' ? '0.1' : '0.5', value: String(qolValue(key)), style: 'width:110px',
        'aria-label': label, oninput: e => { state.qolOpt[key] = e.target.value; qolShell(); } })),
      el('div', { class: 'faint', text: detail }), hint ? el('div', { class: 'muted', text: hint }) : null));
  }
  const tick = (key, title, detail, count) => optionItem({ checked: qolValue(key) === true, title, detail, count,
    onchange: e => { state.qolOpt[key] = e.target.checked; qolShell(); } });
  const names = (f.vip_names || []).length ? ' ' + 'Names found:' + ' ' : '';
  const card = el('div', { class: 'card', id: 'qol-options' },
    el('div', { class: 'form' }, rows,
      el('ul', { class: 'steps', style: 'grid-column:1 / -1' },
        tick('noshake', 'The -noshake command', 'Each player can turn the camera shakes of the map off and on.',
          f.shake_calls),
        tick('noshake_default', 'Start with the camera shakes off', 'Every player starts with them off; -noshake ' +
          'turns them back on.'),
        tick('reveal', 'Reveal the whole map', 'The map starts revealed and stays so.', f.fog_calls),
        tick('vip', 'VIP for everyone', 'Every check of a player name against the map\'s list answers as for a ' +
          'listed name. The same checks may guard the author\'s own commands, which open up too.', f.vip_checks),
        stripIndentItem()),
      names ? el('div', { class: 'faint', style: 'grid-column:1 / -1' }, el('span', { text: 'Names found:' }), ' ',
        el('span', { class: 'mono', translate: 'no', text: f.vip_names.join(', ') })) : null,
      el('div', { style: 'grid-column:1 / -1' },
        el('div', { class: 'shell', id: 'qol-shell' }, '$ ', el('span', { class: 'cmd' }), el('span', { class: 'cursor' })),
        el('button', { class: 'btn primary needs-idle', text: 'Apply the QoL edits', disabled: !!state.running,
          onclick: runQol }))));
  tabBody('qol', head, card, state.qolResult ? qolResult(state.qolResult) : null);
  qolShell();
}

async function runQol() {
  if (state.running) return;
  const options = qolOptions();
  if (!Object.keys(options).length) { toast('Change at least one option first.'); return; }
  status('Applying the QoL edits...');
  try {
    const r = await run('qol_apply', { options, strip_indent: stripIndentOn() }, { label: 'Applying the QoL edits...' });
    state.qolResult = r;
    state.results.qol = r;
    renderQol();
    status(r.outcome === 'ok' ? 'QoL edits written.' : 'The QoL edits stopped.');
    if (r.outcome === 'failed') toast('The QoL edits were not written.', { bad: true });
  } catch (e) {
    failed(e, 'Applying the QoL edits');
    if (e && e.cancelled) { renderQol(); return; }
    const msg = (e && e.message) || String(e);
    const lines = [['bad', 'The QoL edits stopped: ' + msg]];
    if (e && e.trace) e.trace.split('\n').filter(l => l.trim()).forEach(l => lines.push(['info', '  ' + l]));
    state.qolResult = { outcome: 'failed', lines, file: null };
    renderQol();
  }
}

function qolResult(r) {
  const ok = r.outcome === 'ok';
  return el('div', { class: 'card' + (r.outcome === 'failed' ? ' bad' : ''), id: 'result-qol' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'QoL edits: result' }),
      el('span', { class: 'badge ' + (ok ? 'good' : r.outcome === 'failed' ? 'bad' : 'warn'),
        text: ok ? 'Written' : r.outcome === 'failed' ? 'Stopped' : 'Nothing written' })),
    reportLines(r.lines || []),
    el('div', { class: 'foot row', style: 'margin-top:14px' },
      r.file ? el('span', { class: 'faint mono grow', text: r.file }) : null,
      r.file ? folderButton(r.file) : null,
      r.outcome === 'failed' ? el('button', { class: 'btn ghost', text: 'Report a problem', onclick: reportProblem }) :
        null));
}

async function loadTriggers(gen) {
  try {
    const t = await run('triggers', {}, { quiet: true });
    if (gen !== state.gen) return;
    renderTriggers(t);
    setTabState('triggers', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('triggers', 'Reading the triggers', e); }
}

function renderTriggers(t) {
  const notes = (t.notes || []).map(n => el('p', { class: 'muted', text: n }));
  if (!t.categories || !t.categories.length) {
    tabBody('triggers', el('div', { class: 'card' },
      t.error ? el('div', { class: 'report' }, el('div', { class: 'l bad', text: t.error })) :
        el('p', { class: 'muted', text: t.reason || 'No triggers to show.' }),
      notes));
    return;
  }
  const view = el('div', { class: 'card', style: 'min-height:200px' }, el('span', { class: 'faint',
    text: 'Pick a trigger.' }));
  const tree = el('div', { class: 'tree scroll', style: 'padding:8px' }, t.categories.map(c => el('details',
    { open: t.categories.length < 6 }, el('summary', { text: c.name + ' (' + c.triggers.length + ')' }),
    c.triggers.map(g => el('div', { class: 'trig', text: g.name + (g.kind === 'text' ? '  (text)' : '') +
      (g.enabled === false ? '  (off)' : ''), onclick: e => {
      $$('.trig.sel', tree).forEach(x => x.classList.remove('sel')); e.target.classList.add('sel'); showTrigger(g, view);
    } })))));
  const src = t.source === 'map' ? 'the map\'s own trigger files' : 'restored from the script';
  tabBody('triggers', el('div', { class: 'split' }, el('div', {}, el('p', { class: 'muted', text: 'From ' + src + '.' }),
    notes, tree), view));
}

function showTrigger(g, view) {
  const block = (title, cls, lines) => lines && lines.length ? el('div', {}, el('h3', { text: title }),
    lines.map(l => el('div', { class: 'gui-line ' + cls, text: '    '.repeat(l.depth || 0) +
      (typeof l === 'string' ? l : l.text) }))) : null;
  view.replaceChildren(el('h2', { text: g.name }), g.kind === 'text' ? el('pre', { class: 'code', text: g.text || '' }) :
    el('div', {}, block('Events', 'e', g.events), block('Conditions', 'c', g.conditions), block('Actions', 'a',
      g.actions)));
}

function optionItem(o) {
  return el('li', { class: 'step' + (o.disabled ? ' na' : '') },
    el('input', { type: 'checkbox', checked: !!o.checked, disabled: !!o.disabled, onchange: o.onchange }),
    el('div', { class: 'grow' }, el('div', { class: 't' }, o.title, o.tag ? el('span', { class: 'tag', text: o.tag, translate: o.tagIsName ? 'no' : null }) :
      null), o.detail ? el('div', { class: 'd', text: o.detail }) : null),
    o.count !== undefined ? el('span', { class: 'count', text: String(o.count) }) : null);
}

async function loadTranslationGroups(gen) {
  try {
    const r = await run('translation_groups', {}, { quiet: true });
    if (gen !== state.gen) return;
    state.trGroups = r;
  } catch (e) {
    if (gen !== state.gen) return;
    state.trGroups = { state: 'failed', error: (e && e.message) || String(e) };
  }
  renderTranslation();
}

function pickedGroups() {
  const g = state.trGroups;
  if (!g || !g.groups) return null;
  const keys = g.groups.map(x => x.key).filter(k => !state.trSkip.has(k));
  return keys.length === g.groups.length ? null : keys;
}

function translationGroupsBox() {
  const g = state.trGroups;
  if (!g) return el('p', { class: 'faint', text: 'Listing the texts of the map...' });
  if (g.state === 'failed') return el('div', { class: 'report' }, el('div', { class: 'l bad', text: g.error }));
  if (!(g.groups || []).length) return el('p', { class: 'muted', text: 'The map has no text to export.' });
  const all = g.groups.every(x => !state.trSkip.has(x.key));
  const set = on => { state.trSkip = on ? new Set() : new Set(g.groups.map(x => x.key)); renderTranslation(); };
  const total = g.groups.filter(x => !state.trSkip.has(x.key)).reduce((n, x) => n + x.count, 0);
  return el('div', {},
    el('div', { class: 'row', style: 'margin:4px 0 6px' }, el('h3', { class: 'grow', style: 'margin:0',
      text: 'What to export' }), el('span', { class: 'faint', text: total + ' texts' }),
    el('button', { class: 'btn small ghost', text: all ? 'None' : 'All', onclick: () => set(!all) })),
    el('ul', { class: 'steps' }, g.groups.map(x => optionItem({ checked: !state.trSkip.has(x.key), title: x.label,
      tag: x.key, tagIsName: true, count: x.count, onchange: e => {
        if (e.target.checked) state.trSkip.delete(x.key); else state.trSkip.add(x.key);
        renderTranslation(); } }))));
}

function renderTranslation() {
  const tr = state.extras.translation;
  const none = !state.trGroups ||
    (state.trGroups.groups && pickedGroups() !== null && !pickedGroups().length);
  tabBody('translation', el('div', { class: 'card' }, el('h2', { text: 'Export' }),
    el('p', { class: 'lead', text: 'Pick the texts, export them, translate the file, then load it back below.' }),
    translationGroupsBox(),
    imagesOption(),
    el('div', { class: 'row', style: 'margin-top:12px' },
      el('button', { class: 'btn needs-idle', text: 'Export as JSON...', disabled: !!state.running || none,
        onclick: () => exportTexts('json') }),
      el('button', { class: 'btn needs-idle', text: 'Export for Google Translate / DeepL...',
        disabled: !!state.running || none, onclick: () => exportTexts('html') }))),
  machineCard(none),
  el('div', { class: 'card' }, el('h2', { text: 'Import' }),
    el('p', { class: 'lead', text: 'Load the translated file. It is checked first; then tick "Apply the translation" ' +
      'in Fix or Editor.' }),
    el('button', { class: 'btn needs-idle', text: 'Load a translation...', disabled: !!state.running,
      onclick: async () => {
        if (state.running) return;
        const p = await api().pick_file('translation');
        if (!p) return;
        try {
          const r = await run('translation_check', { file: p }, { label: 'Checking the translation...' });
          state.extras.translation = { file: p, check: r };
          renderTranslation(); renderActions();
        } catch (e) { failed(e, 'Checking the translation'); }
      } }),
    tr && tr.check.error ? el('div', { style: 'margin-top:14px' }, el('div', { class: 'report' },
      el('div', { class: 'l bad', text: base(tr.file) + ': ' + tr.check.error })),
    el('button', { class: 'btn small', style: 'margin-top:10px', text: 'Forget this translation', onclick: () => {
      state.extras.translation = null; renderTranslation(); renderActions(); } })) :
    tr ? el('div', { style: 'margin-top:14px' }, el('div', { class: 'notice info', text: base(tr.file) + ': ' +
      (tr.check.ok || 0) + ' texts pass the checks' + (tr.check.rejected && tr.check.rejected.length ? ', ' +
      tr.check.rejected.length + ' left out' : '') + '.' }),
    tr.check.images && !web() ? el('button', { class: 'btn needs-idle', style: 'margin-top:10px',
      text: 'Review the images (' + tr.check.images + ')...', disabled: !!state.running, onclick: () => loadReview() }) :
      null,
    tr.check.rejected && tr.check.rejected.length ? el('div', { class: 'scroll', style: 'margin-top:10px;max-height:300px' },
      el('table', { class: 'grid' }, el('thead', {}, el('tr', {}, el('th', { text: 'Text' }), el('th', { text: 'Why' }))),
        el('tbody', {}, tr.check.rejected.slice(0, 500).map(x => el('tr', {}, el('td', { class: 'mono',
          text: x.id || x.text }), el('td', { class: 'muted', text: x.reason || x.why || '' })))))) : null,
    el('button', { class: 'btn small', style: 'margin-top:10px', text: 'Forget this translation', onclick: () => {
      state.extras.translation = null; state.trReview = null; renderTranslation(); renderActions(); } })) : null),
  reviewCard());
}

function imagesOption() {
  if (web()) return null;
  const m = state.trGroups && state.trGroups.machine;
  const ocr = m && m.ocr;
  if (!ocr) return null;
  return el('label', { style: 'display:flex;gap:8px;align-items:center;margin-top:10px;cursor:pointer' },
    el('input', { type: 'checkbox', checked: state.trImages, onchange: e => { state.trImages = e.target.checked; } }),
    el('span', { text: 'Also read the text in the images (OCR, slower)' }),
    ocr.installed ? null : el('span', { class: 'faint', text: Math.max(1, Math.round(ocr.size / 1048576)) +
      ' MB to download' }));
}

async function loadReview() {
  const tr = state.extras.translation;
  if (!tr || state.running) return;
  try {
    const r = await run('translation_images', { file: tr.file }, { label: 'Drawing the images...' });
    if (r.error) { failed({ message: r.error }, 'Drawing the images'); return; }
    state.trReview = { file: tr.file, images: (r.images || []).map(x => Object.assign(x, {
      entries: x.entries.map(e => Object.assign(e, { apply: !!e.translation, edit: e.translation })) })) };
    renderTranslation();
  } catch (e) { failed(e, 'Drawing the images'); }
}

function reviewCard() {
  const rv = state.trReview;
  if (!rv || !state.extras.translation || state.extras.translation.file !== rv.file) return null;
  const save = async () => {
    if (state.running) return;
    const changes = {};
    rv.images.forEach(x => x.entries.forEach(e => { changes[e.id] = e.apply ? e.edit : ''; }));
    try {
      const r = await run('translation_update', { file: rv.file, changes }, { label: 'Saving the changes...' });
      if (r.error) { failed({ message: r.error }, 'Saving the changes'); return; }
      state.extras.translation.check = r.check;
      rv.images.forEach(x => x.entries.forEach(e => { e.translation = e.apply ? e.edit : ''; }));
      renderTranslation(); renderActions();
      toast('Saved ' + (r.changed || 0) + ' changes to ' + base(rv.file) + '.');
    } catch (e) { failed(e, 'Saving the changes'); }
  };
  return el('div', { class: 'card' }, el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'The images' }),
    el('button', { class: 'btn needs-idle', text: 'Save the changes', disabled: !!state.running, onclick: save })),
    el('p', { class: 'lead', text: 'Each image as it is and as it will be. Fix the English of a line, or untick it to ' +
      'keep the original; "Update preview" redraws the image, "Save the changes" writes them to the translation file.' }),
    rv.images.map(x => reviewImage(x)));
}

function reviewImage(x) {
  const pic = (b64, label) => el('figure', { style: 'margin:0;text-align:center' },
    el('img', { src: 'data:image/png;base64,' + b64, style: 'max-width:100%;image-rendering:pixelated;' +
      'border:1px solid var(--line, #333)' }), el('figcaption', { class: 'faint', text: label }));
  const imgs = x.error ? el('div', { class: 'notice', text: x.error }) :
    el('div', { style: 'display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0' },
      pic(x.original, 'Now'), el('div', { class: 'prev' }, pic(x.preview, 'Translated')));
  const holder = el('div', {}, imgs);
  const refresh = async () => {
    if (state.running) return;
    try {
      const r = await run('translation_image_preview', { entries: x.entries.map(e => ({ id: e.id,
        translation: e.apply ? e.edit : '' })) }, { label: 'Drawing the image...' });
      if (r.error) { failed({ message: r.error }, 'Drawing the image'); return; }
      x.preview = r.preview;
      const prev = holder.querySelector('.prev img');
      if (prev) prev.src = 'data:image/png;base64,' + r.preview;
    } catch (e) { failed(e, 'Drawing the image'); }
  };
  return el('div', { style: 'border-top:1px solid var(--line, #333);padding-top:12px;margin-top:12px' },
    el('div', { class: 'mono faint', translate: 'no', text: x.members.join('  ') }),
    holder,
    x.entries.map(e => el('div', { class: 'row', style: 'margin:6px 0;gap:8px;align-items:center' },
      el('input', { type: 'checkbox', checked: e.apply, title: 'Apply this line',
        onchange: ev => { e.apply = ev.target.checked; } }),
      el('span', { class: 'muted', translate: 'no', style: 'min-width:120px', text: e.text }),
      el('input', { type: 'text', value: e.edit, class: 'grow', style: 'min-width:0',
        oninput: ev => { e.edit = ev.target.value; if (e.edit) e.apply = true; } }))),
    x.error ? null : el('button', { class: 'btn small needs-idle', text: 'Update preview', onclick: refresh }));
}

const MT_LANGUAGES = { zh: 'Chinese', ko: 'Korean', ja: 'Japanese', ru: 'Russian', vi: 'Vietnamese', th: 'Thai' };
const MT_QUALITY = { best: 'Best', fast: 'Fast' };

function machineCard(none) {
  const head = [el('h2', { text: 'Local machine translation' }),
    el('p', { class: 'lead', text: 'Translates the picked texts into English on this computer, with an open ' +
      'translation model. Nothing is sent anywhere: the model is downloaded once, from the program\'s GitHub page.' })];
  if (web()) return el('div', { class: 'card' }, ...head,
    el('p', { class: 'muted', text: 'Only in the program for Windows and Linux.' }));
  const g = state.trGroups;
  if (!g || g.state === 'failed' || !(g.groups || []).length) return el('div', { class: 'card' }, ...head);
  const m = g.machine;
  if (!m || !(m.models || []).length) return el('div', { class: 'card' }, ...head,
    el('p', { class: 'muted', text: 'The texts of this map are not in a language it knows. It translates Chinese, ' +
      'Korean, Japanese, Russian, Vietnamese and Thai into English.' }));
  if (!m.models.some(x => x.quality === state.mtQuality)) state.mtQuality = m.models[0].quality;
  const mb = n => Math.max(1, Math.round(n / 1048576)) + ' MB';
  const size = x => x.installed ? 'already downloaded' : mb(x.size) + ' to download';
  const choice = m.models.length > 1 ? el('div', { class: 'row', style: 'margin:8px 0' },
    m.models.map(x => el('label', { style: 'display:inline-flex;gap:6px;align-items:center;margin-right:18px;' +
      'cursor:pointer' }, el('input', { type: 'radio', name: 'mtq', checked: x.quality === state.mtQuality,
      onchange: () => { state.mtQuality = x.quality; renderTranslation(); } }),
    el('span', { text: MT_QUALITY[x.quality] }), el('span', { class: 'faint', text: size(x) })))) : null;
  const picked = m.models.find(x => x.quality === state.mtQuality);
  return el('div', { class: 'card' }, ...head,
    el('p', {}, el('span', { text: 'From ' + (MT_LANGUAGES[m.language] || m.language) + ' to English.' }),
      m.models.length === 1 ? ' ' : null, m.models.length === 1 ? el('span', { class: 'faint', text: size(picked) }) :
        null),
    choice,
    m.models.length > 1 ? el('p', { class: 'faint', text: 'Best reads game texts better; Fast is a smaller download ' +
      'and takes about half the time.' }) : null,
    el('button', { class: 'btn needs-idle', text: 'Translate on this computer...', disabled: !!state.running || none,
      onclick: () => machineTranslate(picked) }),
    el('p', { class: 'faint', style: 'margin-top:10px', text: 'A machine translation is a first pass: names and ' +
      'some game words come out literal. The file can be reviewed and loaded again before you share the map.' }));
}

async function machineTranslate(model) {
  if (state.running) return;
  const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + '.en.translation.json', 'translation');
  if (!p) return;
  try {
    const r = await run('translation_machine', { file: p, only: pickedGroups(), quality: model.quality,
      images: state.trImages },
      { label: 'Translating on this computer...' });
    if (r.state !== 'done') {
      failed({ message: r.error || (r.state === 'no_text' ? 'The map has no text to export.' :
        'The translation did not finish.') }, 'Translating on this computer');
      return;
    }
    model.installed = true;
    state.extras.translation = { file: p, check: r.check };
    renderTranslation(); renderActions();
    toast('Translated ' + (r.translated || 0) + ' of ' + (r.entries || 0) + ' texts into English. Tick "Apply the ' +
      'translation" in Fix or Editor to write them into a copy of the map.',
      { actions: [[showLabel('Show'), () => api().open_folder(p)]] });
  } catch (e) { failed(e, 'Translating on this computer'); }
}

async function exportTexts(kind) {
  if (state.running) return;
  const ext = kind === 'html' ? '.translation.html' : '.translation.json';
  const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + ext,
    kind === 'html' ? 'translation_html' : 'translation');
  if (!p) return;
  try {
    const r = await run('translation_export', { file: p, only: pickedGroups(), images: kind === 'json' &&
      state.trImages }, { label: 'Exporting the texts...' });
    if (r.state !== 'done') {
      failed({ message: r.error || (r.state === 'no_text' ? 'The map has no text to export.' :
        'The export did not finish.') }, 'Exporting the texts');
      return;
    }
    toast('Exported ' + (r.entries || 0) + ' texts to ' + base(p) + '.' + (r.linked_added ? ' ' + r.linked_added +
      ' of them are from files left out: the script compares the same text, so they must be translated together.' :
      ''), { actions: [[showLabel('Show'), () => api().open_folder(p)]] });
  } catch (e) { failed(e, 'Exporting the texts'); }
}

function renderCompare(result) {
  const pick = el('button', { class: 'btn needs-idle', text: 'Pick the other version...', disabled: !!state.running,
    onclick: async () => {
      if (state.running) return;
      const p = await api().pick_file('map');
      if (!p) return;
      try {
        const r = await run('compare', { other: p }, { label: 'Comparing the two maps...' });
        renderCompare(Object.assign(r, { other: p }));
      } catch (e) { failed(e, 'Comparing'); }
    } });
  const parts = [];
  if (result) {
    const f = result.files || {};
    if (result.error) parts.push(el('div', { class: 'report' }, el('div', { class: 'l bad', text: result.error })));
    const list = (title, items, fmt) => items && items.length ? el('div', {}, el('h3', { text: title + ' (' +
      items.length + ')' }), el('div', { class: 'scroll', style: 'max-height:220px;padding:6px 10px' },
      items.slice(0, 2000).map(x => el('div', { class: 'mono', text: fmt ? fmt(x) : (typeof x === 'string' ? x :
        x.name || JSON.stringify(x)) })))) : null;
    parts.push(el('p', { class: 'muted', text: 'This map against ' + base(result.other) + '.' }),
      list('Files only in the other', f.added), list('Files only in this one', f.removed), list('Files changed',
        f.changed), list('Map info', result.info && result.info.changed, x => x.field + ': ' + JSON.stringify(x.a) +
        '  ->  ' + JSON.stringify(x.b)),
      list('Objects', result.objects && [].concat(...Object.entries(result.objects).map(([file, d]) =>
        ['added', 'removed', 'changed'].map(k => (d[k] || []).map(o => file + '  ' + k + '  ' +
          (typeof o === 'string' ? o : (o.id || '') + (o.name ? ' (' + o.name + ')' : '')) +
          (o.fields ? ': ' + o.fields.map(x => x.field + (x.level ? '[' + x.level + ']' : '')).join(', ') : '')))
          .flat()))),
      list('Script functions', result.script && [].concat(...['added', 'removed', 'changed'].map(k =>
        (result.script[k] || []).map(x => k + '  ' + (x.name || x))))),
      list('Strings', result.strings && [].concat(...['added', 'removed', 'changed'].map(k =>
        (result.strings[k] || []).map(x => k + '  ' + (x.id || x))))));
  }
  tabBody('compare', el('div', { class: 'card' }, el('h2', { text: 'Compare two versions' }),
    el('p', { class: 'lead', text: 'What changed against another version of this map.' }), pick, ...parts));
}

function renderPort() {
  const s = state.open ? state.open.summary : null;
  const platform = s && /kk|j2b/.test(s.script || '') ? 'The KK script is turned back into JASS first.' : '';
  const r = state.portResult;
  tabBody('port',
    el('div', { class: 'card' },
      el('h2', { text: 'Port to Reforged' }),
      el('p', { class: 'lead', text: 'For KK or M16 maps (DzAPI, japi, JN): fills in the platform natives, ' +
        'makes the save local and ports the menus. Saves the map and a report next to it.' }),
      platform ? el('p', { class: 'muted', text: platform }) : null,
      el('p', { class: 'muted', text: 'Big maps take minutes.' }),
      packagesBox(),
      el('ul', { class: 'steps', style: 'margin:6px 0 4px' },
        optionItem({ checked: state.portMemory !== false, title: 'Neutralize memory hacks',
          detail: 'What read the old game\'s memory (smart cast, control groups, exit hooks) breaks.',
          onchange: e => { state.portMemory = e.target.checked; } }),
        optionItem({ checked: state.portTextures !== false, title: 'Decrypt the KK textures',
          detail: 'The ones the platform keeps encrypted (BLX1), which the game cannot read.',
          onchange: e => { state.portTextures = e.target.checked; } }),
        optionItem({ checked: state.portIcons !== false, title: 'Fix the green icons',
          detail: 'Makes the disabled art of the imported icons (a dead hero, another unit\'s items).',
          onchange: e => { state.portIcons = e.target.checked; } }),
        optionItem({ checked: state.portBalance === true, title: 'Balance huge numbers',
          detail: 'Scales life, damage, mana and armor down so the biggest fit the game\'s limit, keeping the proportions.',
          onchange: e => { state.portBalance = e.target.checked; } }),
        optionItem({ checked: state.portGameFiles === true, title: 'Remove the game\'s own files',
          detail: 'Icons, textures and interface models the map carries with the game\'s own path. Try it if the ' +
            'game crashes on the ported map.',
          onchange: e => { state.portGameFiles = e.target.checked; } }),
        optionItem({ checked: state.portLossy === true, title: 'If above 512 MiB, make the art smaller',
          detail: 'Halves the biggest textures and makes WAV sounds mono at 22 kHz, only until the map fits the ' +
            'game\'s 512 MiB. This loses quality.',
          onchange: e => { state.portLossy = e.target.checked; } }),
        stripIndentItem()),
      el('div', { class: 'foot' }, el('button', { class: 'btn primary needs-idle', text: 'Port to Reforged',
        disabled: !!state.running, onclick: runPort }))),
    r ? portResult(r) : null);
}

async function loadDiagnoseLists(gen) {
  try {
    const [logs, crashes, replays] = await Promise.all([run('diag_logs', {}, { quiet: true }),
      run('crash_list', {}, { quiet: true }), run('replay_list', {}, { quiet: true }).catch(() => null)]);
    if (gen !== state.gen) return;
    state.diag.logs = logs;
    state.diag.crashes = crashes;
    state.diag.replays = replays;
    renderDiagnose();
  } catch (e) { }
}

function renderDiagnose() {
  const d = state.diag;
  const s = state.open ? state.open.summary : {};
  const jass = !/lua/.test((s && s.script) || '');
  tabBody('diagnose',
    el('div', { class: 'card' },
      el('h2', { text: 'Diagnostic copy' }),
      el('p', { class: 'lead', text: 'A copy of the map that writes what it does to a log while you play it: the ' +
        'functions the game started and never finished (their thread most likely stopped there), the Lua errors, the ' +
        'last things that ran. Play it until the problem happens, then read the log below.' }),
      jass ? el('ul', { class: 'steps', style: 'margin:6px 0 4px' },
        optionItem({ checked: d.mode === 'all', title: 'Mark every function',
          detail: 'Finer, but the extra work can itself stop long loops: use it when the first copy does not say ' +
            'enough.', onchange: e => { d.mode = e.target.checked ? 'all' : 'entry'; renderDiagnose(); } }),
        optionItem({ checked: d.mode === 'init', title: 'Load markers',
          detail: 'For a map that hangs on the loading screen: every step of the load writes its own file at once, ' +
            'so the last one says where it stopped.', onchange: e => { d.mode = e.target.checked ? 'init' : 'entry';
            renderDiagnose(); } })) : null,
      el('div', { class: 'foot' }, el('button', { class: 'btn primary needs-idle', text: 'Make a diagnostic copy',
        disabled: !!state.running, onclick: runDiagMake }))),
    d.result ? diagMakeResult(d.result) : null,
    el('div', { class: 'card' },
      el('h2', { text: 'Read a diagnostic log' }),
      el('p', { class: 'muted', text: 'The game writes it to Documents\\Warcraft III\\CustomMapData\\DevosMapDoctor.' }),
      diagList((d.logs && d.logs.logs) || [], x => [x.name, when(x.modified)], x => readDiagLog(x.path)),
      el('div', { class: 'foot' }, el('button', { class: 'btn needs-idle', text: 'Choose a log...',
        disabled: !!state.running, onclick: async () => {
          const f = await api().pick_file('log');
          if (f) readDiagLog(f);
        } }))),
    d.log ? diagLogResult(d.log) : null,
    el('div', { class: 'card' },
      el('h2', { text: 'Read a crash report' }),
      el('p', { class: 'muted', text: 'When the game closes it writes a report to Documents\\Warcraft III\\Errors; ' +
        'its log (Logs\\War3Log.txt) also says what the map asked for and the game refused.' }),
      diagList((d.crashes && d.crashes.reports) || [], x => [x.name, (x.kind || '') + ' in ' + (x.module || '?'),
        x.map ? base(x.map) : ''], x => readCrash(x.path)),
      el('ul', { class: 'steps', style: 'margin:6px 0 4px' },
        optionItem({ checked: d.checkMap, title: 'Check the open map against the game',
          detail: 'For a crash in ClientSdk.dll: counts the images and models the open map carries at the game\'s ' +
            'own paths (needs Warcraft III installed; slower).',
          onchange: e => { d.checkMap = e.target.checked; } })),
      el('div', { class: 'foot row' },
        d.crashes && d.crashes.log ? el('button', { class: 'btn needs-idle', text: 'Read the game\'s log',
          disabled: !!state.running, onclick: () => readCrash(d.crashes.log) }) : null,
        el('button', { class: 'btn needs-idle', text: 'Choose a file...', disabled: !!state.running,
          onclick: async () => {
            const f = await api().pick_file('crash');
            if (f) readCrash(f);
          } }))),
    d.crash ? diagCrashResult(d.crash) : null,
    el('div', { class: 'card' },
      el('h2', { text: 'Read a replay' }),
      el('p', { class: 'muted', text: 'A replay (.w3g) says who left and when, the chat, the sync and frame events and ' +
        'the state checksum of every turn. The game keeps one when it closes (TempReplay.w3g) and one when a game ends ' +
        '(LastReplay.w3g).' }),
      diagList((d.replays && d.replays.replays) || [], x => [x.name, x.kind, when(x.modified)], x => readReplay(x.path)),
      el('div', { class: 'foot' }, el('button', { class: 'btn needs-idle', text: 'Choose a replay...',
        disabled: !!state.running, onclick: async () => {
          const f = await api().pick_file('replay');
          if (f) readReplay(f);
        } }))),
    d.replay ? diagReportCard('Replay', d.replay, d.replay.error ? [] : [
      ['Players', (d.replay.players || []).map(p => p.name || '?')],
      ['Who left', (d.replay.leaves || []).map(l => clock((l.t || 0) / 1000) + '  ' + (l.name || '?'))],
      ['Chat', (d.replay.chat || []).slice(-40).map(c => clock((c.t || 0) / 1000) + '  ' + (c.name || '?') + ': ' +
        (c.text || ''))]]) : null);
}

async function readReplay(path) {
  if (state.running) return;
  try {
    state.diag.replay = await run('replay_read', { file: path }, { label: 'Reading the replay...' });
  } catch (e) {
    failed(e, 'Reading the replay');
    return;
  }
  renderDiagnose();
}

function when(t) { return t ? new Date(t * 1000).toLocaleString() : ''; }

function diagList(items, cols, onread) {
  if (!items.length) return null;
  return el('div', { class: 'report', style: 'margin:6px 0' }, items.slice(0, 8).map(x =>
    el('div', { class: 'row', style: 'gap:10px;align-items:center' },
      el('span', { class: 'grow mono faint', translate: 'no', text: cols(x).filter(Boolean).join('  ·  ') }),
      el('button', { class: 'btn small needs-idle', text: 'Read', disabled: !!state.running, onclick: () => onread(x) }))));
}

async function runDiagMake() {
  if (state.running) return;
  status('Making the diagnostic copy...');
  try {
    const r = await run('diag_make', { mode: state.diag.mode }, { label: 'Making the diagnostic copy...' });
    state.diag.result = r;
    status(r.outcome === 'ok' ? 'Diagnostic copy saved.' : 'The diagnostic copy was not made.');
  } catch (e) {
    failed(e, 'Making the diagnostic copy');
    state.diag.result = { outcome: 'failed', lines: [['bad', (e && e.message) || String(e)]] };
  }
  renderDiagnose();
}

function diagMakeResult(r) {
  const ok = r.outcome === 'ok';
  return el('div', { class: 'card' + (ok ? '' : ' bad') },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'Diagnostic copy: result' }),
      el('span', { class: 'badge ' + (ok ? 'good' : 'bad'), text: ok ? 'Saved' : 'Stopped' })),
    reportLines(r.lines || []),
    el('div', { class: 'foot row', style: 'margin-top:14px' },
      r.file ? el('span', { class: 'faint mono grow', text: r.file }) : null,
      r.file ? folderButton(r.file) : null));
}

async function readDiagLog(path) {
  if (state.running) return;
  try {
    state.diag.log = await run('diag_read', { file: path }, { label: 'Reading the log...' });
  } catch (e) {
    failed(e, 'Reading the log');
    return;
  }
  renderDiagnose();
}

async function readCrash(path) {
  if (state.running) return;
  try {
    state.diag.crash = await run('crash_read', { file: path, check_map: state.diag.checkMap },
      { label: 'Reading the crash report...' });
  } catch (e) {
    failed(e, 'Reading the crash report');
    return;
  }
  renderDiagnose();
}

function diagReportCard(title, r, folds) {
  return el('div', { class: 'card' + (r.error ? ' bad' : '') },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: title }),
      el('button', { class: 'btn small', text: 'Copy as text', onclick: async () => {
        await copyText(r.text || r.error || ''); toast('The report is in the clipboard.'); } })),
    r.error ? reportLines([['bad', r.error]]) : reportLines(r.findings || []),
    folds.filter(f => f && f[1].length).map(([summary, rows]) => el('details', { style: 'margin-top:8px' },
      el('summary', { text: summary }),
      el('pre', { class: 'mono', translate: 'no', style: 'white-space:pre-wrap;margin:6px 0 0',
        text: rows.join('\n') }))));
}

function diagLogResult(r) {
  return diagReportCard('Diagnostic log: ' + (r.map || ''), r, r.error ? [] : [
    ['Open functions (started, finished, last start)', (r.open || []).map(o =>
      o.name + (o.waits ? ' (waits)' : '') + '  ' + o.started + '  ' + o.finished + '  ' + (o.last || 0).toFixed(2))],
    ['Lua errors', (r.errors || []).map(e => e.times + 'x  ' + (e.first || 0).toFixed(1) + ' s  ' + e.where + ': ' +
      e.message)],
    ['The last events', (r.events || []).slice(-60).map(e => (e.time || 0).toFixed(2) + '  ' + e.name + '  x' +
      e.times)]]);
}

function diagCrashResult(r) {
  const lg = r.log || {};
  return diagReportCard('Crash report', r, r.error ? [] : [
    ['Models the game could not create', Object.entries(lg.models || {}).map(([p, n]) => n + 'x  ' + (p || '(empty)'))],
    ['Interface frames with names that are too long', Object.entries(lg.frames_long || {}).map(([k, v]) =>
      v[0] + ':' + v[1] + '  ' + k)],
    ['The modules on the stack', ((r.crash || {}).exception || {}).modules || []],
    ['Files at the game\'s own paths', (r.overrides || {}).sample || []]]);
}

function packagesBox() {
  const list = state.portPackages || [];
  return el('div', { style: 'margin:10px 0' },
    el('h3', { text: 'Art packages (optional)' }),
    el('p', { class: 'muted', text: 'Add the platform client\'s art packages the map needs (models, icons, ' +
      'sounds), newest first.' }),
    list.length ? el('ul', { class: 'steps' }, list.map((p, i) => el('li', { class: 'step' },
      el('div', { class: 'grow mono', text: (i + 1) + '. ' + base(p) }),
      i ? el('button', { class: 'btn small', text: 'Up', onclick: () => {
        const l = list.slice(); [l[i - 1], l[i]] = [l[i], l[i - 1]]; state.portPackages = l; renderPort(); } }) : null,
      el('button', { class: 'btn small ghost', text: 'Remove', onclick: () => {
        state.portPackages = list.filter((_x, k) => k !== i); renderPort(); } })))) : null,
    el('button', { class: 'btn small', text: 'Add an art package...', onclick: async () => {
      const p = await api().pick_file('package');
      if (!p) return;
      state.portPackages = list.concat([p]);
      renderPort();
    } }),
    web() ? null : ' ',
    web() ? null : el('button', { class: 'btn small', text: 'Add a folder...', title: 'A folder of loose art files (the ones ' +
      'a map reads from the game folder with "Allow Local Files")', onclick: async () => {
      const p = await api().pick_folder();
      if (!p) return;
      state.portPackages = list.concat([p]);
      renderPort();
    } }));
}

async function runPort() {
  if (state.running) return;
  status('Porting the map...');
  try {
    const r = await run('port', { packages: state.portPackages || [], memory: state.portMemory !== false,
      icons: state.portIcons !== false, textures: state.portTextures !== false, balance: state.portBalance === true,
      game_files: state.portGameFiles === true, lossy: state.portLossy === true, strip_indent: stripIndentOn() },
      { label: 'Porting the map to Reforged...' });
    state.portResult = r;
    state.results.port = r;
    renderPort();
    status(r.outcome === 'ok' ? 'Ported.' : 'The port stopped.');
  } catch (e) {
    failed(e, 'Port to Reforged');
    if (e && e.cancelled) return;
    const msg = (e && e.message) || String(e);
    const lines = [['bad', 'The port stopped: ' + msg]];
    if (e && e.trace) e.trace.split('\n').filter(l => l.trim()).forEach(l => lines.push(['info', '  ' + l]));
    state.portResult = { outcome: 'failed', lines: lines, port: { error: msg } };
    renderPort();
  }
}

function portResult(r) {
  const p = r.port || {};
  const badge = r.outcome === 'ok' ? ['good', 'Ported'] : ['bad', 'Stopped'];
  const stubs = p.stubs || [];
  return el('div', { class: 'card', id: 'result-port' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'Port to Reforged: result' }),
      el('span', { class: 'badge ' + badge[0], text: badge[1] })),
    el('div', { class: 'badges' },
      p.g1 !== undefined && p.g1 !== null ? el('span', { class: 'badge ' + (p.g1 ? 'good' : 'bad'),
        text: 'Compiler gate G1: ' + (p.g1 ? 'pass' : 'fail') }) : null,
      p.g2 !== undefined && p.g2 !== null ? el('span', { class: 'badge ' + (p.g2 ? 'good' : 'bad'),
        text: 'Compiler gate G2: ' + (p.g2 ? 'pass' : 'fail') }) : null,
      p.declared ? el('span', { class: 'badge', text: p.implemented + ' of ' + p.declared +
        ' platform natives implemented' }) : null,
      el('span', { class: 'badge ' + (stubs.length ? 'warn' : 'good'), text: stubs.length + ' called stub' +
        (stubs.length === 1 ? '' : 's') })),
    reportLines(r.lines),
    stubs.length ? el('div', {}, el('h3', { text: 'Stubs the map calls' }),
      el('div', { class: 'scroll', style: 'max-height:280px' }, el('table', { class: 'grid' },
        el('thead', {}, el('tr', {}, el('th', { text: 'Native' }), el('th', { text: 'Calls' }),
          el('th', { text: 'Functions' }), el('th', { text: 'Triggers' }))),
        el('tbody', {}, stubs.map(s => el('tr', {}, el('td', { class: 'mono', text: s.native }),
          el('td', { text: String(s.calls) }), el('td', { class: 'mono', text: (s.functions || []).slice(0, 8).join(', ') +
            ((s.functions || []).length > 8 ? ' ...' : '') }), el('td', { text: (s.triggers || []).join(', ') }))))))) :
      null,
    el('div', { class: 'foot row', style: 'margin-top:14px' },
      r.file ? folderButton(r.file) : null,
      r.report ? folderButton(r.report, 'Show the report') : null,
      el('button', { class: 'btn', text: 'Copy report', onclick: async () => {
        await copyText(plainReport(r.lines)); toast('The report is in the clipboard.'); } }),
      el('button', { class: 'btn ghost', text: 'Report a problem', onclick: reportProblem })));
}

function languagePicker(saved) {
  const i18n = window.doctorI18n;
  const sel = $('#lang');
  if (!i18n || !sel) return;
  if (saved && saved !== i18n.lang) i18n.setLang(saved, true);
  sel.replaceChildren(...Object.entries(i18n.langs).map(([code, name]) => el('option', { value: code, text: name })));
  sel.value = i18n.lang;
  sel.onchange = () => {
    i18n.setLang(sel.value);
    state.settings.lang = sel.value;
    saveSettings();
  };
}

function wire() {
  $('#btnOpen').onclick = pickMap;
  $('#btnOpen2').onclick = pickMap;
  $('#btnReport').onclick = reportProblem;
  $('#btnAbout').onclick = showAbout;
  $('#btnCancel').onclick = () => { if (state.running) api().cancel(state.running); };
  $$('#modes button').forEach(b => { b.onclick = () => selectMode(b.dataset.mode); });
  $$('.subtabs button').forEach(b => { b.onclick = () => selectTab(b.dataset.tab); });
  const drop = $('#drop');
  document.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('over'); });
  document.addEventListener('dragleave', e => { if (!e.relatedTarget) drop.classList.remove('over'); });
  document.addEventListener('drop', e => { e.preventDefault(); drop.classList.remove('over'); });
}

window.addEventListener('pywebviewready', async () => {
  wire();
  const h = await api().hello();
  state.hello = h;
  state.settings = h.settings || {};
  $('#version').textContent = 'v' + h.version;
  $('#where').textContent = web() ? ' · runs in your browser' : ' · runs on your computer';
  languagePicker(h.settings && h.settings.lang);
  showRecent();
  if (h.map) openMap(h.map);
  api().check_update();
});
