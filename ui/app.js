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
  trGroups: null, trSkip: new Set(),
  extras: { card: null, translation: null, models: null, modelNames: null, singlePlayer: null, portraits: null,
    dataPointers: null, kkTextures: null, disabledIcons: null, uabi: null, preload: null },
  cheatpacks: null, cheatPack: { id: null, options: {}, result: null },
  rawcodes: null,
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
      size: state.open ? state.open.size : null, stage: null, marks: [] };
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
      if (!job.quiet) {
        job.stage = { label: ev.label, at: (Date.now() - job.started) / 1000 };
        job.marks.push(job.stage);
      }
      if (!job.quiet && state.running === ev.job) $('#jobLabel').textContent = ev.label;
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
function learnTime(job) {
  const secs = (Date.now() - job.started) / 1000;
  if (secs < 1) return;
  const timing = state.settings.timing = Object.assign({}, state.settings.timing);
  for (const k of new Set([job.key, job.task])) {
    const h = Object.assign({ n: 0, stages: {} }, timing[k]);
    const mix = (old, now) => old === undefined || old === null || !h.n ? now : old * 0.6 + now * 0.4;
    h.secs = mix(h.secs, secs);
    if (job.size) h.mbps = mix(h.mbps, secs / Math.max(job.size / 1e6, 0.1));
    const stages = Object.assign({}, h.stages);
    for (const m of job.marks) stages[m.label] = mix(stages[m.label], m.at / secs);
    h.stages = stages;
    h.n = Math.min(h.n + 1, 20);
    timing[k] = h;
  }
  saveSettings();
}

function estimate(job) {
  const t = state.settings.timing || {};
  const h = t[job.key] || t[job.task];
  if (!h) return null;
  const now = (Date.now() - job.started) / 1000;
  let total = job.size && h.mbps ? h.mbps * job.size / 1e6 : h.secs;
  const st = job.stage, f = st && h.stages ? h.stages[st.label] : null;
  if (f > 0.05 && st.at > 1) total = total > 0 ? (total + 2 * st.at / f) / 3 : st.at / f;
  if (!(total > 0)) return null;
  return { frac: Math.min(now / total, 0.97), left: Math.max(total - now, 0) };
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
    e.frac = job.shown = Math.max(job.shown || 0, e.frac);
    const full = Math.round(e.frac * BAR);
    bar = '[' + '\u2588'.repeat(full) + '\u2591'.repeat(BAR - full) + '] ' + Math.round(e.frac * 100) + '%';
    tail = e.left >= 1 ? '~' + clock(e.left) + ' left' : 'almost done';
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
  state.images = {};
  state.imageData = {};
  state.results = {};
  state.portResult = null;
  state.portPackages = [];
  state.extras = { card: null, translation: null, models: null, modelNames: null, singlePlayer: null, portraits: null,
    dataPointers: null, kkTextures: null, disabledIcons: null, uabi: null, preload: null };
  state.cheatpacks = null;
  state.cheatPack = { id: null, options: {}, result: null };
  state.trGroups = null;
  state.trSkip = new Set();
  state.rawcodes = null;
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
    renderTranslation();
    renderCompare();
    renderPort();
    setTabState('translation', 'ready');
    setTabState('compare', 'ready');
    setTabState('port', 'ready');
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

function renderHeader() {
  const o = state.open, s = o.summary;
  $('#mapTitle').textContent = o.name;
  $('#mapPath').textContent = o.map + '  (' + mb(o.size) + ')';
  const b = [];
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
  fix: ['models', 'modelNames', 'portraits', 'dataPointers', 'kkTextures', 'disabledIcons', 'uabi', 'preload',
    'singlePlayer', 'card', 'translation', 'stripIndent', 'shrink'],
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
    if (k === 'stripIndent') out.push({ key: 'x:stripIndent', label: STRIP_INDENT.title, detail: STRIP_INDENT.detail,
      on: stripIndentOn(), applies: true, group: 'extra' });
    if (k === 'shrink') out.push({ key: 'x:shrink', label: 'Make the map smaller, losing nothing',
      detail: 'Recompresses every file and stores duplicates once. Slow on big maps.',
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
  'x:translation': 'translation', 'x:stripIndent': 'strip-indent', 'x:shrink': 'shrink' };

function shellLine(action) {
  const card = $('.action[data-action="' + action + '"]');
  if (!card) return;
  const flags = [];
  for (const box of $$('input[data-key]', card)) {
    if (!box.checked) continue;
    const k = box.dataset.key;
    const f = /^(dados|data):/.test(k) ? 'data' : FLAGS[k] || k.replace(/^x:/, '').replace(/[:_]/g, '-');
    if (!flags.includes(f)) flags.push(f);
  }
  const name = state.open ? state.open.name : base(state.map);
  $('.shell .cmd', card).textContent = 'doctor ' + action + ' "' + name + '"' +
    flags.map(f => ' --' + f).join('');
}

function renderAction(action) {
  const a = ACTIONS[action];
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
  if (extras.card && state.extras.card) params.extras.card = state.extras.card;
  if (extras.translation && state.extras.translation) params.extras.translation = state.extras.translation.file;
  if (extras.stripIndent) params.extras.strip_indent = true;
  if (extras.shrink) params.extras.shrink = { recompress: true, blp: true, dedup: true };
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

const TABS = ['card', 'reforged', 'files', 'script', 'cheatpacks', 'triggers', 'translation', 'compare', 'port'];
const TAB_DATA = { card: loadCard, files: loadFiles, script: loadScript, cheatpacks: loadCheatpacks,
  triggers: loadTriggers, reforged: checkReforgedQuietly };

const MODES = { fix: ['fix', 'reforged'], editor: ['editor', 'card', 'triggers'], port: ['port'],
  cheatpacks: ['cheatpacks'], translation: ['translation'], inspect: ['files', 'script', 'compare'] };
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
  for (const name of ['card', 'files', 'script', 'cheatpacks', 'triggers']) {
    if (gen !== state.gen) return;
    await TAB_DATA[name](gen);
  }
  if (gen === state.gen) await loadTranslationGroups(gen);
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
  const r = state.reforged;
  if (!r) { tabBody('reforged', el('div', { class: 'card muted', text: 'Checking...' })); return; }
  const sev = { blocker: 'bad', warning: 'warn', info: 'info' };
  const verdict = { 'v-yes': 'Yes, it should run on Reforged.', 'v-probably': 'Probably: nothing known stops it.',
    'v-no': 'Not as it is: see the blockers below.', 'v-unknown': 'Cannot tell.' }[r.verdict_code] || 'Cannot tell.';
  const fix = { doctor: '"Fix map" or "Open in World Editor" takes care of it.', port: 'It needs a port, not a fix.',
    none: '' };
  tabBody('reforged', el('div', { class: 'card' }, el('h2', { text: verdict }),
    el('p', { class: 'lead', text: 'A "yes" means none of the measured problems is there.' }),
    (r.items || []).length ? el('div', { class: 'report' }, r.items.map(it => el('div', { class: 'step' },
      el('span', { class: 'badge ' + (sev[it.severity] || ''), text: it.severity }),
      el('div', {}, el('div', { text: it.text }), fix[it.fix] ? el('div', { class: 'd muted', text: fix[it.fix] }) :
        null)))) : el('p', { class: 'muted', text: 'Nothing found.' })));
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
  const filter = el('input', { class: 'field', type: 'text', placeholder: 'Filter by name or kind',
    style: 'max-width:320px' });
  const rows = el('tbody');
  const preview = el('div', { class: 'preview' }, el('span', { class: 'faint', text: 'Click a file to see it.' }));
  const selected = new Set();
  const draw = () => {
    const q = filter.value.toLowerCase();
    rows.replaceChildren(...f.files.filter(x => !q || x.name.toLowerCase().includes(q) || x.kind.includes(q))
      .slice(0, 3000).map(x => {
        const box = el('input', { type: 'checkbox', checked: selected.has(x.name), onclick: e => { e.stopPropagation();
          if (e.target.checked) selected.add(x.name); else selected.delete(x.name); } });
        const tr = el('tr', { class: 'click', onclick: () => {
          $$('tr.sel', rows).forEach(r => r.classList.remove('sel')); tr.classList.add('sel'); showPreview(x, preview);
        } }, el('td', {}, box), el('td', { class: 'mono', text: x.name, title: x.about || '' },
          ...lintBadges(x.name)), el('td', { text: x.kind }),
        el('td', { style: 'text-align:right', text: (x.size / 1024).toFixed(x.size < 10240 ? 1 : 0) + ' KB' }));
        return tr;
      }));
  };
  filter.addEventListener('input', draw);
  draw();
  tabBody('files', rawcodesCard(), el('div', { class: 'card' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: f.files.length + ' files' +
      (f.unnamed && f.unnamed.length ? ', ' + f.unnamed.length + ' without a name' : '') }), filter,
      el('button', { class: 'btn needs-idle', text: 'Extract selected...', disabled: !!state.running,
        onclick: async () => {
          if (state.running) return;
          if (!selected.size) { toast('Tick the files to extract first.'); return; }
          const dir = await api().pick_folder();
          if (!dir) return;
          try {
            const r = await run('extract', { names: Array.from(selected), folder: dir }, { label: 'Extracting...' });
            if (r.error) { failed({ message: r.error }, 'Extracting'); return; }
            const n = (r.written || []).length, bad = r.failed || [], kept = (r.exists || []).length;
            if (bad.length) toast(bad.length + (bad.length === 1 ? ' file' : ' files') + ' could not be extracted: ' +
              bad.slice(0, 5).map(x => x.name + (x.reason ? ' (' + x.reason + ')' : '')).join(', ') +
              (bad.length > 5 ? ', ...' : ''), { bad: true, sticky: true });
            toast('Extracted ' + n + (n === 1 ? ' file' : ' files') + (kept ? ', ' + kept + ' already there' : '') +
              '.', { actions: [[showLabel('Show'), () => api().open_folder(dir)]] });
          } catch (e) { failed(e, 'Extracting'); }
        } })),
    f.error ? el('div', { class: 'report' }, el('div', { class: 'l bad', text: f.error })) : null,
    (f.notes || []).map(n => el('p', { class: 'muted', text: n })),
    lintSummary(f),
    el('div', { class: 'split', style: 'margin-top:12px' },
      el('div', { class: 'scroll' }, el('table', { class: 'grid' }, el('thead', {}, el('tr', {}, el('th', {}),
        el('th', { text: 'Name' }), el('th', { text: 'Kind' }), el('th', { text: 'Size', style: 'text-align:right' }))),
      rows)), preview)));
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
      text: JSON.stringify(p.info, null, 1) }));
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
      el('ul', { class: 'steps', style: 'grid-column:1 / -1' }, stripIndentItem()),
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
    const r = await run('cheatpack_inject', { pack, options: cheatpackOptions(), strip_indent: stripIndentOn() },
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
  const none = state.trGroups && state.trGroups.groups && pickedGroups() !== null && !pickedGroups().length;
  tabBody('translation', el('div', { class: 'card' }, el('h2', { text: 'Export' }),
    el('p', { class: 'lead', text: 'Pick the texts, export them, translate the file, then load it back below.' }),
    translationGroupsBox(),
    el('div', { class: 'row', style: 'margin-top:12px' },
      el('button', { class: 'btn needs-idle', text: 'Export as JSON...', disabled: !!state.running || none,
        onclick: () => exportTexts('json') }),
      el('button', { class: 'btn needs-idle', text: 'Export for Google Translate / DeepL...',
        disabled: !!state.running || none, onclick: () => exportTexts('html') }))),
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
    tr.check.rejected && tr.check.rejected.length ? el('div', { class: 'scroll', style: 'margin-top:10px;max-height:300px' },
      el('table', { class: 'grid' }, el('thead', {}, el('tr', {}, el('th', { text: 'Text' }), el('th', { text: 'Why' }))),
        el('tbody', {}, tr.check.rejected.slice(0, 500).map(x => el('tr', {}, el('td', { class: 'mono',
          text: x.id || x.text }), el('td', { class: 'muted', text: x.reason || x.why || '' })))))) : null,
    el('button', { class: 'btn small', style: 'margin-top:10px', text: 'Forget this translation', onclick: () => {
      state.extras.translation = null; renderTranslation(); renderActions(); } })) : null));
}

async function exportTexts(kind) {
  if (state.running) return;
  const ext = kind === 'html' ? '.translation.html' : '.translation.json';
  const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + ext,
    kind === 'html' ? 'translation_html' : 'translation');
  if (!p) return;
  try {
    const r = await run('translation_export', { file: p, only: pickedGroups() }, { label: 'Exporting the texts...' });
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
        stripIndentItem()),
      el('div', { class: 'foot' }, el('button', { class: 'btn primary needs-idle', text: 'Port to Reforged',
        disabled: !!state.running, onclick: runPort }))),
    r ? portResult(r) : null);
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
    } }));
}

async function runPort() {
  if (state.running) return;
  status('Porting the map...');
  try {
    const r = await run('port', { packages: state.portPackages || [], memory: state.portMemory !== false,
      icons: state.portIcons !== false, textures: state.portTextures !== false, balance: state.portBalance === true,
      strip_indent: stripIndentOn() },
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
