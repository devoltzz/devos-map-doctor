// Devo's Map Doctor 1.4: the page. It never touches a map: every job runs in the program's worker
// (window.pywebview.api.start), and the events come back through window.doctor.onEvent.
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
// the site (1.6) has no folder to show: what a job saved is downloaded
const web = () => !!(state.hello && state.hello.web);
const showLabel = what => web() ? 'Download' : what;
const folderButton = (path, what) => el('button', { class: 'btn', text: showLabel(what || 'Show in folder'),
  onclick: () => api().open_folder(path) });
function status(text) { $('#status').textContent = text; }

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
  try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* the old way below */ }
  const ta = el('textarea', {}, text);
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand('copy');
  ta.remove();
  return ok;
}

// an image the engine sends as raw RGBA rows (base64), drawn into a canvas
function rgbaCanvas(img, maxSide) {
  const c = el('canvas', { width: img.width, height: img.height });
  const bytes = Uint8ClampedArray.from(atob(img.rgba), ch => ch.charCodeAt(0));
  c.getContext('2d').putImageData(new ImageData(bytes, img.width, img.height), 0, 0);
  if (maxSide && Math.max(img.width, img.height) > maxSide) c.style.width = maxSide + 'px';
  return c;
}

// ------------------------------------------------------------------ the bridge
const state = {
  hello: null, settings: {}, map: null, open: null, jobs: {}, running: null, results: {},
  // `gen` counts the maps opened: what a job of an earlier map brings back is dropped; the quiet jobs of the map
  // (the tabs loading in the background) are cancelled when another one opens
  gen: 0, tabState: {}, quietJobs: new Set(), images: {}, imageData: {},
  extras: { card: null, translation: null, models: null, modelNames: null, singlePlayer: null, portraits: null,
    dataPointers: null, uabi: null, preload: null },
  // the Cheatpacks tab: the answer of the backend (the packs this map's script language can take) and what the page
  // picked (the pack id, the value of each option of it, and the result of the last injection)
  cheatpacks: null, cheatPack: { id: null, options: {}, result: null },
  // the Files tab: the answer of "Read the raw codes", and null until the button is pressed (nothing is read on its own)
  rawcodes: null,
};

const api = () => window.pywebview.api;

// the events of a job whose id the bridge has not returned yet (a worker that ends before `start` comes back): kept
// here and replayed when the job registers; one that nobody claims is dropped after a while
const pendingEvents = {};

// `start` is awaited outside the Promise: when it throws (TEMP full, the worker blocked) the caller's catch gets the
// error instead of a job that never ends
async function run(task, params, opts) {
  opts = opts || {};
  // `quiet`: the site runs the tabs that load in the background in a worker of their own (the exe ignores it)
  const id = await api().start(task, Object.assign({ map: state.map }, params || {},
    opts.quiet ? { quiet: true } : {}));
  return new Promise((resolve, reject) => {
    state.jobs[id] = { task, resolve, reject, started: Date.now(), label: opts.label, quiet: opts.quiet };
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
      if (!job.quiet && state.running === ev.job) $('#jobLabel').textContent = ev.label;
      if (job.onProgress) job.onProgress(ev.label);
      return;
    }
    delete state.jobs[ev.job];
    state.quietJobs.delete(ev.job);
    if (state.running === ev.job) hideJob();
    if (ev.type === 'result') job.resolve(ev.data);
    // `kept`: the output already had its name when the cancel came (a "Fix map" cancelled during the extras)
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
  timer = setInterval(() => { $('#jobTime').textContent = clock((Date.now() - t0) / 1000); }, 500);
  setBusy(true);
}
function hideJob() {
  state.running = null;
  clearInterval(timer);
  $('#jobCard').classList.add('hidden');
  setBusy(false);
}
function setBusy(busy) {
  // a button that is off for a reason of its own (nothing to do for this map) carries data-off and stays off
  $$('.needs-idle').forEach(b => { b.disabled = busy || b.hasAttribute('data-off'); });
  $('#btnOpen').disabled = busy;
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

// ------------------------------------------------------------------ settings
async function saveSettings() { try { await api().save_settings(state.settings); } catch (e) { /* not fatal */ } }

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

// ------------------------------------------------------------------ opening a map
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
  state.lastError = null;                   // the problem report of this map must not carry the error of the last one
  state.card = state.files = state.reforged = null;
  state.images = {};
  state.imageData = {};
  state.results = {};
  state.portResult = null;
  state.portPackages = [];
  state.extras = { card: null, translation: null, models: null, modelNames: null, singlePlayer: null, portraits: null,
    dataPointers: null, uabi: null, preload: null };
  state.cheatpacks = null;
  state.cheatPack = { id: null, options: {}, result: null };
  state.rawcodes = null;
  TABS.forEach(n => setTabState(n, 'wait'));
  $('#welcome').classList.add('hidden');
  $('#mapview').classList.remove('hidden');
  $('#btnOpen').classList.remove('hidden');
  $('#mapTitle').textContent = base(path);
  $('#mapPath').textContent = path;
  $('#badges').replaceChildren(el('span', { class: 'badge', text: 'Checking...' }));
  $('#diagLines').replaceChildren();
  $('#actions').replaceChildren();
  $('#results').replaceChildren();
  $$('.tab').forEach(t => { if (t.id !== 'tab-actions') t.replaceChildren(); });
  selectTab('actions');
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

// ------------------------------------------------------------------ the map header

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

// the map's images, asked once per map (the header thumbnail and the map card share them); null when there is none
function imageOf(which) {
  if (!state.images[which]) {
    state.images[which] = run('card_image', { which }, { quiet: true }).catch(() => null);
  }
  return state.images[which];
}

async function loadThumb(gen) {
  const img = await imageOf('minimap');
  if (gen !== state.gen || !img) return;     // no minimap: the empty frame stays
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
    // 1.5.3: the extras of the new checks
    if (r.portraits && r.portraits.fixable) { state.extras.portraits = r.portraits; renderActions(); }
    if (r.data_pointers && r.data_pointers.fixable) { state.extras.dataPointers = r.data_pointers; renderActions(); }
    if (r.uabi && r.uabi.distinct) { state.extras.uabi = r.uabi; renderActions(); }
    if (r.preload && (r.preload.units || r.preload.abilities)) { state.extras.preload = r.preload; renderActions(); }
    // 1.5.6: os nomes de modelo que a ferramenta Model_Encrypt renomeou
    if (r.model_names && r.model_names.fixable) { state.extras.modelNames = r.model_names; renderActions(); }
  } catch (e) {
    if (gen !== state.gen) return;
    const badge = $('#reforgedBadge');
    if (badge) badge.textContent = 'Runs on Reforged? could not check';
    tabFailed('reforged', 'Checking whether it runs on Reforged', e);
  }
}

// ------------------------------------------------------------------ the two actions
const ACTIONS = {
  fix: { title: 'Fix map', suffix: '_fixed', label: 'Fixing the map...',
    lead: 'Saves a copy without the protection and with the 3.0 fixes.' },
  editor: { title: 'Open in World Editor', suffix: '_editor',
    label: 'Preparing the map for the World Editor...',
    lead: 'Saves a copy the World Editor opens, triggers back as GUI.' },
};
const EXTRA_STEPS = {
  fix: ['models', 'modelNames', 'portraits', 'dataPointers', 'uabi', 'preload', 'singlePlayer', 'card', 'translation',
    'shrink'],
  editor: ['singlePlayer', 'card', 'translation'],
};

function choices(action) {
  // what the user picked last time (when "remember" is on), over the defaults of this map
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
    // a translation whose check failed (`error`) is shown in its tab, never offered here
    if (k === 'translation' && x.translation && !x.translation.check.error) out.push({ key: 'x:translation',
      label: 'Apply the translation',
      detail: base(x.translation.file) + ', from the Translation tab.', on: true, applies: true, group: 'extra' });
    if (k === 'shrink') out.push({ key: 'x:shrink', label: 'Make the map smaller, losing nothing',
      detail: 'Recompresses every file and stores duplicates once. Slow on big maps.',
      on: false, applies: true, group: 'extra' });
  }
  return out;
}

function renderActions() {
  if (!state.open) return;
  const box = $('#actions');
  box.replaceChildren(...Object.keys(ACTIONS).map(renderAction));
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
        saveSettings(); renderActions(); } }), ' show the ' + hidden + ' steps not needed') : null));
  return card;
}

function stepItem(action, s, checked) {
  const locked = s.locked && s.applies;
  const box = el('input', { type: 'checkbox', checked: !!checked, disabled: locked || !s.applies,
    'data-key': s.key, onchange: () => rememberChoice(action) });
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
  if (extras.uabi) params.extras.uabi = true;
  if (extras.preload) params.extras.preload = true;
  if (extras.card && state.extras.card) params.extras.card = state.extras.card;
  if (extras.translation && state.extras.translation) params.extras.translation = state.extras.translation.file;
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
        el('tbody', {}, ch.files.map(f => el('tr', {}, el('td', { class: 'mono', text: f.file }),
          el('td', { text: f.how }), el('td', { class: 'muted', text: f.why })))))) : null,
      ch.notes.map(n => el('div', { class: 'muted', text: n }))) : null,
    el('div', { class: 'foot row', style: 'margin-top:14px' },
      r.file ? folderButton(r.file) : null,
      el('button', { class: 'btn', text: 'Copy report', onclick: async () => {
        await copyText(plainReport(r.lines)); toast('The report is in the clipboard.'); } }),
      el('button', { class: 'btn ghost', text: 'Report a problem', onclick: reportProblem })));
  const old = $('#result-' + action);
  if (old) old.replaceWith(card); else $('#results').prepend(card);
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function plainReport(lines) {
  return lines.map(([style, text]) => (style === 'title' ? '## ' : '') + text).join('\n');
}

// ------------------------------------------------------------------ report a problem
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

// ------------------------------------------------------------------ updates
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

// ------------------------------------------------------------------ tabs
// Every tab but Actions stays locked, with a spinner on its button, until ALL of its information is in: the data
// tabs load in the background as soon as the map is checked, one after the other (a big map in several workers at
// once would take that much more memory); "Runs on Reforged?" opens when its check ends; Translation and Compare
// when the map is checked.
const TABS = ['card', 'reforged', 'files', 'script', 'cheatpacks', 'triggers', 'translation', 'compare', 'port'];
const TAB_DATA = { card: loadCard, files: loadFiles, script: loadScript, cheatpacks: loadCheatpacks,
  triggers: loadTriggers, reforged: checkReforgedQuietly };

function setTabState(name, st) {
  state.tabState[name] = st;
  const b = $('#tabs button[data-tab="' + name + '"]');
  if (!b) return;
  b.disabled = st === 'wait';
  b.classList.toggle('loading', st === 'wait');
  b.classList.toggle('failed', st === 'failed');
  b.title = st === 'wait' ? 'Loading: the tab opens when its information is in.' :
    st === 'failed' ? 'Loading failed: open the tab to try again.' : '';
}

async function loadTabsInBackground(gen) {
  for (const name of ['card', 'files', 'script', 'cheatpacks', 'triggers']) {
    if (gen !== state.gen) return;
    await TAB_DATA[name](gen);
  }
}

function selectTab(name) {
  if (name !== 'actions' && state.tabState[name] === 'wait') return;
  $$('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === name));
  $$('.tab').forEach(t => t.classList.toggle('hidden', t.id !== 'tab-' + name));
}

// the empty parts (null, false) are skipped, as in el(): replaceChildren() would show them as the text "null"
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
    selectTab('actions');
    TAB_DATA[name](state.gen);
  } })));
}

// ------------------------------------------------------------------ the map card
// |cffRRGGBB...|r and |n as the game shows them
function colored(text) {
  const out = el('div', { class: 'colorpreview' });
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
  // the commands as plain text, ONE PER LINE: the empty match ("any message") is not a command to type, and the "..."
  // of a prefix match is not part of the command
  const chatCommandText = (list) => (list || [])
    .map(x => typeof x === 'string' ? x : String(x.text || ''))
    .map(t => t.trim()).filter(t => t).join('\n');
  const infoCard = el('div', { class: 'card' }, el('h2', { text: 'What the map says about itself' }),
    el('div', { class: 'form' },
      el('label', { text: 'Language' }), el('div', { style: 'padding-top:7px', text: describeLanguage(info.language) }),
      el('label', { text: 'Save' }), el('div', { style: 'padding-top:7px', text: describeSave(info.save) }),
      el('label', { text: 'Chat commands' }), el('div', { style: 'padding-top:7px' },
        (info.chat_commands || []).length ? el('div', {},
          el('div', { class: 'mono', style: 'white-space:pre-wrap',
            text: info.chat_commands.map(x => typeof x === 'string' ? x : x.text === '' ? '(any message)' :
              x.text + (x.exact === false ? '...' : '')).join('   ') }),
          chatCommandText(info.chat_commands) ? el('button', { class: 'btn small ghost', style: 'margin-top:6px',
            text: 'Copy all (one per line)', onclick: async () => {
              await copyText(chatCommandText(info.chat_commands));
              toast('The commands are in the clipboard.');
            } }) : null) :
          el('span', { class: 'muted', text: 'none found in the script' }))));
  tabBody('card',
    el('div', { class: 'card' }, el('h2', { text: 'Map card' }),
      el('p', { class: 'lead', text: 'Changes go into the next copy ("Apply the map card changes" in ' +
        'Actions).' }),
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
  // the image came in with the card (loadCard waits for both before the tab opens)
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
    // the size the map already uses (the minimap is square, a power of two): the picture is fitted to it
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
  // a file the browser cannot decode (corrupt, or cut at the 32 MB the bridge reads): nothing changes, and it says so
  img.onerror = () => toast('The image ' + base(p) + ' could not be read: pick a valid PNG, JPG or BMP under 32 MB.',
    { bad: true });
  img.src = 'data:image/' + (ext === 'jpg' ? 'jpeg' : ext) + ';base64,' + b64;
}

// ------------------------------------------------------------------ runs on Reforged?
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

// ------------------------------------------------------------------ files
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
            // `written` is a list of {name, path, size}; `failed` of {name, reason}; `exists` the ones left as they were
            const n = (r.written || []).length, bad = r.failed || [], kept = (r.exists || []).length;
            if (bad.length) toast(bad.length + (bad.length === 1 ? ' file' : ' files') + ' could not be extracted: ' +
              bad.slice(0, 5).map(x => x.name + (x.reason ? ' (' + x.reason + ')' : '')).join(', ') +
              (bad.length > 5 ? ', ...' : ''), { bad: true, sticky: true });
            toast('Extracted ' + n + (n === 1 ? ' file' : ' files') + (kept ? ', ' + kept + ' already there' : '') +
              '.', { actions: [[showLabel('Show'), () => api().open_folder(dir)]] });
          } catch (e) { failed(e, 'Extracting'); }
        } })),
    // the module never raises: when the map could not be read, its reason is here (and the list is empty)
    f.error ? el('div', { class: 'report' }, el('div', { class: 'l bad', text: f.error })) : null,
    (f.notes || []).map(n => el('p', { class: 'muted', text: n })),
    lintSummary(f),
    el('div', { class: 'split', style: 'margin-top:12px' },
      el('div', { class: 'scroll' }, el('table', { class: 'grid' }, el('thead', {}, el('tr', {}, el('th', {}),
        el('th', { text: 'Name' }), el('th', { text: 'Kind' }), el('th', { text: 'Size', style: 'text-align:right' }))),
      rows)), preview)));
}

// 1.5.3: the import checks of a file (import_lint)
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
  // one request counter per box: the answer of an earlier click (a slow model) must not replace the one shown
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

// ------------------------------------------------------------------ the raw codes
// The four-character ids the map's object data uses (units, items, abilities, buffs, upgrades, doodads). The ids that
// are not ASCII are the PG family: a protector renamed the objects to hide what they are. Nothing is read until the
// user presses the button; the answer stays in the state, so the card is the same when the tab is drawn again.
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
      // the job itself failed: the red line the other tabs show, and the reason under it
      body.replaceChildren(el('div', { class: 'report' },
        el('div', { class: 'l bad', text: 'Reading the raw codes failed.' }),
        el('div', { class: 'l info', text: (e && e.message) || String(e) })));
    }
    btn.disabled = false;
  } });
  return el('div', { class: 'card' },
    el('div', { class: 'row' }, el('h2', { class: 'grow', text: 'Raw codes' }), btn),
    el('p', { class: 'lead', text: 'The four-character ids the object data uses. Non-ASCII ones are the PG ' +
      'family.' }),
    body);
}

// how many of the ids are not printable ASCII (the PG family). It counts the UNIQUE ids of the kinds: the per-source
// "ansii" can repeat the same id under two sources, and the "text" escapes the bytes Python reads as a line break, so
// counting it would say less than the truth. The test catches both the control bytes of the PG family and the
// surrogates of the ids above ASCII.
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

// the answer of the backend: the summary line, one table row per kind (its first ids as a preview), the note, and the
// two buttons that hand over the whole list the same way the Script tab exports its script
function drawRawcodes(body, r) {
  if (r.error) {
    body.replaceChildren(el('div', { class: 'report' }, el('div', { class: 'l bad', text: r.error })));
    return;
  }
  const kinds = r.kinds || [];
  const total = r.total === undefined || r.total === null ? kinds.reduce((n, k) => n + (k.count || 0), 0) : r.total;
  const ansii = nonAsciiIds(r.text, kinds);
  body.replaceChildren(
    el('p', { class: 'lead', text: total + ' raw codes, ' + ansii + ' of them not ASCII (the PG family).' }),
    kinds.length ? el('div', { class: 'scroll', style: 'max-height:320px' }, el('table', { class: 'grid' },
      el('thead', {}, el('tr', {}, el('th', { text: 'Kind' }), el('th', { text: 'From' }), el('th', { text: 'Count' }),
        el('th', { text: 'Not ASCII' }), el('th', { text: 'First ids' }))),
      el('tbody', {}, kinds.map(k => {
        const ids = k.ids || [];
        return el('tr', {}, el('td', { class: 'mono', text: k.kind }), el('td', { class: 'muted', text: k.source }),
          el('td', { text: String(k.count === undefined || k.count === null ? ids.length : k.count) }),
          el('td', { class: k.ansii ? 'warn' : 'faint', text: String(k.ansii || 0) }),
          el('td', { class: 'mono', text: ids.slice(0, 8).join('  ') + (ids.length > 8 ? '  ...' : '') }));
      })))) : el('p', { class: 'muted', text: 'No object data to read in this map.' }),
    r.note ? el('p', { class: 'muted', text: r.note }) : null,
    r.text ? el('div', { class: 'row', style: 'margin-top:12px' },
      el('button', { class: 'btn', text: 'Copy all', onclick: async () => {
        await copyText(r.text);
        toast('The raw codes are in the clipboard.');
      } }),
      el('button', { class: 'btn', text: 'Save as...', onclick: async () => {
        const p = await api().pick_save(base(state.map).replace(/\.\w+$/, '') + '_rawcodes.txt', 'text');
        if (p) { await api().write_text(p, r.text); toast('Saved ' + base(p) + '.'); }
      } })) : null);
}

// ------------------------------------------------------------------ script
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

// 1.5.3: "Script checks" (script_checks.py): the handle leaks by how often they run, the start-up the script never
// calls, the globals it reads and never sets
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

// ------------------------------------------------------------------ cheat packs
// A cheat pack (JJCP, NZCP, Devo's CP, OzzyCP) is a script of its own that goes INTO the map's script: the archive
// keeps the packs in common/cheatpacks/ and reads them as data, never runs them. The backend hands back only the packs
// of the language the map's script is written in (a Lua map gets the Lua packs, a JASS map the JASS ones), with the
// options of each pack; this tab lists them, sets the options and injects the chosen one (always obfuscated), which
// writes an edited copy of the map next to the original.
async function loadCheatpacks(gen) {
  try {
    const s = await run('cheatpacks', {}, { quiet: true });
    if (gen !== state.gen) return;
    if (s.error) { tabFailed('cheatpacks', 'Reading the cheat packs', { message: s.error }); return; }
    state.cheatpacks = s;
    // the page starts on the first pack; a pack the map still offers stays picked (this runs again on "Try again")
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
  // what the map already carries comes first: that card only reads, the cards under it inject a pack
  tabBody('cheatpacks', head, cheatpackFound(d), packs.map(cheatpackCard),
    state.cheatPack.result ? cheatpackResult(state.cheatPack.result) : null);
}

// The packs the map's OWN script already carries (the "found" of the backend). Read-only: nothing here is injected,
// the pack is only named, with what the player types to call it, where it was found and what gave it away.
function cheatpackFound(d) {
  const found = d.found || [];
  return el('div', { class: 'card', id: 'cheatpacks-found' },
    el('h2', { text: 'Cheat packs already in this map' }),
    found.length ? el('p', { class: 'lead', text: found.length +
      (found.length === 1 ? ' cheat pack' : ' cheat packs') + ' in the map\'s own script.' }) : null,
    found.length ? el('ul', { class: 'steps' }, found.map(cheatpackFoundItem)) :
      el('p', { class: 'muted', text: 'No cheat pack found in this map\'s script.' }));
}

// one detection: the name, the activator the player types (in mono, highlighted: it is the thing to try in game), where
// it was found and the line of evidence, with the confidence as a badge ("certain", or "guess" when it is not proved)
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
      el('div', { style: 'grid-column:1 / -1' }, el('button', { class: 'btn primary needs-idle',
        text: 'Inject the cheat pack', disabled: !!state.running, onclick: runCheatpack }))) : null);
}

// one option: a text field, or a tick box that spans the two columns of the form; the value is kept in the state as the
// string the backend reads ('true'/'false' for a bool, as the pack's own default comes)
function cheatpackField(o) {
  const v = state.cheatPack.options[o.key];
  const value = v === undefined ? o.default : v;
  if (o.kind === 'bool') {
    return [el('label', { class: 'show-na', style: 'grid-column:1 / -1;padding-top:0' },
      el('input', { type: 'checkbox', checked: String(value).toLowerCase() === 'true', onchange: e => {
        state.cheatPack.options[o.key] = e.target.checked ? 'true' : 'false'; } }), ' ' + o.label)];
  }
  return [el('label', { text: o.label }),
    el('input', { class: 'field', type: 'text', value: value === null || value === undefined ? '' : String(value),
      oninput: e => { state.cheatPack.options[o.key] = e.target.value; } })];
}

// the options of the chosen pack, each one with its default when the page never touched it
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
    const r = await run('cheatpack_inject', { pack, options: cheatpackOptions() },
      { label: 'Injecting the cheat pack...' });
    state.cheatPack.result = r;
    state.results.cheatpacks = r;
    renderCheatpacks();
    status(r.outcome === 'ok' ? 'Cheat pack injected.' : 'The injection stopped.');
    if (r.outcome !== 'ok') toast('The cheat pack was not injected.', { bad: true });
  } catch (e) {
    failed(e, 'Injecting the cheat pack');
    if (e && e.cancelled) { renderCheatpacks(); return; }
    // the worker itself failed: the result card says what, with the trace, so it can be copied and reported
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

// ------------------------------------------------------------------ triggers
async function loadTriggers(gen) {
  try {
    const t = await run('triggers', {}, { quiet: true });
    if (gen !== state.gen) return;
    renderTriggers(t);
    setTabState('triggers', 'ready');
  } catch (e) { if (gen === state.gen) tabFailed('triggers', 'Reading the triggers', e); }
}

function renderTriggers(t) {
  // the module never raises: `error` is why nothing was read, `notes` what it saw on the way (the map's own trigger
  // files the editor 3.0 cannot read, the game's data missing)
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

// ------------------------------------------------------------------ translation
function renderTranslation() {
  const tr = state.extras.translation;
  tabBody('translation', el('div', { class: 'card' }, el('h2', { text: 'Translate the map' }),
    el('p', { class: 'lead', text: 'Export every text a player sees, translate it, load it back. The ' +
      'checks run before anything is applied.' }),
    el('p', { class: 'muted', text: 'Two formats: JSON, or a web page for Google Translate or DeepL; load ' +
      'the translated page back here.' }),
    el('div', { class: 'row' },
      el('button', { class: 'btn needs-idle', text: 'Export texts...', disabled: !!state.running,
        onclick: () => exportTexts('json') }),
      el('button', { class: 'btn needs-idle', text: 'Export for machine translation...', disabled: !!state.running,
        onclick: () => exportTexts('html') }),
      el('button', { class: 'btn needs-idle', text: 'Load a translation...', disabled: !!state.running,
        onclick: async () => {
          if (state.running) return;
          const p = await api().pick_file('translation');
          if (!p) return;
          try {
            const r = await run('translation_check', { file: p }, { label: 'Checking the translation...' });
            // a check with `error` (the file or the map cannot be read) is kept to be shown, never applied
            state.extras.translation = { file: p, check: r };
            renderTranslation(); renderActions();
          } catch (e) { failed(e, 'Checking the translation'); }
        } })),
    tr && tr.check.error ? el('div', { style: 'margin-top:14px' }, el('div', { class: 'report' },
      el('div', { class: 'l bad', text: base(tr.file) + ': ' + tr.check.error })),
    el('button', { class: 'btn small', style: 'margin-top:10px', text: 'Forget this translation', onclick: () => {
      state.extras.translation = null; renderTranslation(); renderActions(); } })) :
    tr ? el('div', { style: 'margin-top:14px' }, el('div', { class: 'notice info', text: base(tr.file) + ': ' +
      (tr.check.ok || 0) + ' texts pass the checks' + (tr.check.rejected && tr.check.rejected.length ? ', ' +
      tr.check.rejected.length + ' left out' : '') + '. Tick "Apply the translation" in Actions.' }),
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
    const r = await run('translation_export', { file: p }, { label: 'Exporting the texts...' });
    // the module never raises: 'failed' comes with `error`, 'no_text' writes nothing
    if (r.state !== 'done') {
      failed({ message: r.error || (r.state === 'no_text' ? 'The map has no text to export.' :
        'The export did not finish.') }, 'Exporting the texts');
      return;
    }
    toast('Exported ' + (r.entries || 0) + ' texts to ' + base(p) + '.', { actions: [[showLabel('Show'), () =>
      api().open_folder(p)]] });
  } catch (e) { failed(e, 'Exporting the texts'); }
}

// ------------------------------------------------------------------ compare
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
    // the module never raises: `error` is why the comparison stopped (the other map cannot be read)
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

// ------------------------------------------------------------------ start
// ------------------------------------------------------------------ port to Reforged (1.5)
// A map made for the KK or M16 platform (Chinese and Korean RPGs of patch 1.27/1.28) runs on Reforged only after its
// platform natives get a body, its save becomes a local save and its menus become Reforged frames. The port does it
// in one go and saves <map>_reforged.w3x and <map>_reforged.report.txt next to the original.
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
      // 1.5.1: the memory hacks of patch 1.2x (JN maps): the Reforged equivalents always; the rest neutralized when ticked
      el('label', { class: 'show-na', style: 'display:block;margin:6px 0 10px' },
        el('input', { type: 'checkbox', checked: state.portMemory !== false, onchange: e => {
          state.portMemory = e.target.checked; } }),
        ' Neutralize memory hacks: what read the old game\'s memory (smart cast, control groups, ' +
        'exit hooks) breaks.'),
      el('div', { class: 'foot' }, el('button', { class: 'btn primary needs-idle', text: 'Port to Reforged',
        disabled: !!state.running, onclick: runPort }))),
    r ? portResult(r) : null);
}

// the art packages: the platform client loaded models and icons from a package outside the map (.mix, .asi, a plugin
// .dll or a plain .mpq). They are read as data, never run; the first in the list wins when two have the same file.
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
    const r = await run('port', { packages: state.portPackages || [], memory: state.portMemory !== false },
      { label: 'Porting the map to Reforged...' });
    state.portResult = r;
    state.results.port = r;
    renderPort();
    status(r.outcome === 'ok' ? 'Ported.' : 'The port stopped.');
  } catch (e) {
    failed(e, 'Port to Reforged');
    if (e && e.cancelled) return;
    // the worker itself failed: the result card says what, with the trace, so it can be copied and reported
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

function wire() {
  $('#btnOpen').onclick = pickMap;
  $('#btnOpen2').onclick = pickMap;
  $('#btnReport').onclick = reportProblem;
  $('#btnCancel').onclick = () => { if (state.running) api().cancel(state.running); };
  $$('#tabs button').forEach(b => { b.onclick = () => selectTab(b.dataset.tab); });
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
  showRecent();
  if (h.map) openMap(h.map);
  api().check_update();
});
