// The queue of several maps: one action on every map of a folder.
'use strict';

(() => {
  const ACTIONS = {
    fix: { label: 'Fix map', params: () => ({ options: null, extras: {} }) },
    editor: { label: 'Open in World Editor', params: () => ({ options: null, extras: {} }) },
    port: { label: 'Port to Reforged', params: () => ({ packages: [], memory: true }) },
    cheatpack_inject: { label: 'Add a cheat pack', perMap: true },
  };
  const MAP = /\.w3[xmn]$/i;
  const OURS = /_(fixed|editor|reforged)( \(\d+\))?\.w3[xmn]$/i;
  const canWriteFolder = typeof window.showDirectoryPicker === 'function';
  let running = false;
  let stop = false;

  async function exists(dir, name) {
    try { await dir.getFileHandle(name); return true; } catch (e) { return false; }
  }

  async function freeName(dir, name) {
    const dot = name.lastIndexOf('.');
    const stem = dot > 0 ? name.slice(0, dot) : name, ext = dot > 0 ? name.slice(dot) : '';
    let n = name;
    for (let k = 2; await exists(dir, n); k++) n = stem + ' (' + k + ')' + ext;
    return n;
  }

  async function write(dir, name, bytes) {
    const n = await freeName(dir, name);
    const w = await (await dir.getFileHandle(n, { create: true })).createWritable();
    await w.write(bytes);
    await w.close();
    return n;
  }

  async function pickFolder() {
    const dir = await window.showDirectoryPicker({ id: 'doctor-maps', mode: 'readwrite' });
    const files = [];
    for await (const [name, h] of dir.entries()) {
      if (h.kind === 'file' && MAP.test(name) && !OURS.test(name)) files.push(await h.getFile());
    }
    files.sort((a, b) => a.name.localeCompare(b.name));
    return { dir, files };
  }

  function pickFiles() {
    return new Promise(resolve => {
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = true;
      input.accept = '.w3x,.w3m,.w3n';
      input.onchange = () => resolve({ dir: null, files: Array.from(input.files).filter(f => MAP.test(f.name)) });
      input.addEventListener('cancel', () => resolve(null));
      input.click();
    });
  }

  const BADGE = { running: ['info', 'Working'], ok: ['good', 'Done'], partial: ['warn', 'Partly done'],
    nothing: ['info', 'Nothing to do'], ready: ['info', 'Ready'],
    failed: ['bad', 'Stopped'], skipped: ['warn', 'Skipped'], cancelled: ['info', 'Cancelled'] };

  function row(file) {
    const state = el('span', { class: 'badge', text: 'Waiting' });
    const note = el('div', { class: 'faint', text: window.mb ? window.mb(file.size) : '' });
    const extra = el('div');
    const li = el('li', { class: 'step' }, el('div', { class: 'grow' }, el('div', { class: 'mono', text: file.name }),
      note, extra), state);
    return { li, extra, set(kind, text) {
      const b = BADGE[kind] || ['info', kind];
      state.className = 'badge ' + b[0];
      state.textContent = b[1];
      if (text !== undefined) note.textContent = text;
    }, note(text) { note.textContent = text; } };
  }

  function packChooser(item, list) {
    const packs = list.packs || [];
    const select = el('select', { class: 'field' }, packs.map(p => el('option', { value: p.id, text: p.title })));
    const fields = el('div', { class: 'row', style: 'flex-wrap:wrap;gap:8px;margin-top:6px' });
    const values = {};
    const show = () => {
      const pack = packs.find(p => p.id === select.value);
      const keep = item.pack === select.value;
      fields.replaceChildren(...(pack ? pack.options : []).map(o => {
        if (!keep || !(o.key in values)) values[o.key] = o.default;
        const input = el('input', { class: 'field', type: 'text', value: values[o.key],
          style: 'width:15em;height:auto;margin:0;flex:none',
          title: o.note ? o.label + ' -- ' + o.note : o.label, oninput: e => { values[o.key] = e.target.value; } });
        return el('label', { class: 'faint', style: 'display:flex;flex-direction:column;gap:3px;font-size:12.5px' },
          o.label, input);
      }));
      item.pack = select.value;
    };
    const def = packs.find(p => p.default) || packs[0];
    if (def) select.value = def.id;
    select.onchange = () => { for (const k of Object.keys(values)) delete values[k]; show(); };
    show();
    item.choice = () => ({ pack: select.value, options: Object.assign({}, values) });
    item.copyFrom = other => {
      const c = other.choice();
      if (!packs.some(p => p.id === c.pack)) return false;
      select.value = c.pack;
      for (const k of Object.keys(values)) delete values[k];
      Object.assign(values, c.options);
      item.pack = c.pack;
      show();
      return true;
    };
    item.r.extra.style.textAlign = 'left';
    item.r.extra.replaceChildren(el('div', { class: 'row', style: 'gap:8px;margin-top:6px' },
      el('span', { class: 'faint', style: 'white-space:nowrap', text: (list.language || '').toUpperCase() + ' script' }),
      select), fields);
  }

  async function readPacks(picked) {
    const W = window.doctorWeb;
    for (const item of picked) {
      if (stop) { item.r.set('cancelled', ''); continue; }
      if (item.file.size > W.sizeLimit) {
        item.r.set('skipped', 'Above ' + Math.round(W.sizeLimit / 1048576) + ' MB: use the Windows program.');
        continue;
      }
      item.r.set('running', 'Reading the script...');
      item.path = W.addPicked(item.file, '/maps');
      const ev = await W.run('cheatpacks', { map: item.path }, label => item.r.note(label));
      if (ev.type !== 'result') { item.r.set('failed', ev.message || 'The engine stopped.'); continue; }
      const list = ev.data || {};
      if (!(list.packs || []).length) {
        item.r.set('skipped', list.why || list.error || 'No cheat pack fits this map.');
        continue;
      }
      packChooser(item, list);
      item.params = () => item.choice();
      item.r.set('ready', window.mb ? window.mb(item.file.size) : '');
    }
  }

  async function runQueue(action, picked, list, foot) {
    const W = window.doctorWeb;
    const zipped = [];
    let done = 0;
    for (const item of picked) {
      const { file, r } = item;
      if (ACTIONS[action].perMap && !item.params) continue;
      if (stop) { r.set('cancelled', ''); continue; }
      if (file.size > W.sizeLimit) {
        r.set('skipped', 'Above ' + Math.round(W.sizeLimit / 1048576) + ' MB: use the Windows program.');
        continue;
      }
      r.set('running', 'Starting...');
      const path = item.path || W.addPicked(file, '/maps');
      const params = item.params ? item.params() : ACTIONS[action].params();
      const ev = await W.run(action, Object.assign({ map: path }, params), label => r.note(label));
      if (ev.type === 'cancelled') { r.set('cancelled', ''); continue; }
      if (ev.type !== 'result') { r.set('failed', ev.message || 'The engine stopped.'); continue; }
      const res = ev.data || {};
      const outs = [res.file, res.report].filter(Boolean);
      const saved = [];
      for (const p of outs) {
        try {
          const got = await W.read(p);
          if (picked.dir) {
            saved.push(await write(picked.dir, got.name, got.bytes));
            await W.remove(p);
          } else {
            zipped.push(p);
            saved.push(got.name);
          }
        } catch (e) {
          r.set('failed', 'Could not save the result: ' + (e && e.message || e));
        }
      }
      const kind = res.outcome === 'ok' ? 'ok' : res.outcome || 'failed';
      const why = (res.lines || []).find(l => l[0] === 'bad') || (res.lines || []).find(l => l[0] === 'warn');
      r.set(kind, saved.length ? (picked.dir ? 'Saved ' : 'In the zip: ') + saved.join(', ') :
        (why ? why[1].trim() : 'Nothing was written.'));
      done += saved.length ? 1 : 0;
    }
    if (!picked.dir && zipped.length) {
      const z = await W.zip(zipped, 'Devos Map Doctor results.zip');
      W.saveBytes(z.bytes, z.name);
      for (const p of zipped) await W.remove(p);
    }
    foot.replaceChildren(el('span', { class: 'muted', text: stop ? 'Stopped.' :
      done + ' of ' + picked.length + ' maps written' + (picked.dir ? ' into the folder.' : ', in the zip.') }));
  }

  function card() {
    const select = el('select', { class: 'field', style: 'width:auto' }, Object.entries(ACTIONS).map(([k, a]) =>
      el('option', { value: k, text: a.label })));
    const list = el('ul', { class: 'steps' });
    const foot = el('div', { class: 'foot row', style: 'margin-top:10px' });
    const start = el('button', { class: 'btn', text: canWriteFolder ? 'Pick a folder...' : 'Pick maps...' });
    const cancel = el('button', { class: 'btn ghost hidden', text: 'Stop' });
    cancel.onclick = async () => { stop = true; await window.doctorWeb.cancelAll(); };
    const busy = on => {
      running = on;
      start.disabled = on;
      select.disabled = on;
      cancel.classList.toggle('hidden', !on);
    };
    const go = async (action, picked) => {
      busy(true);
      stop = false;
      try {
        await runQueue(action, picked, list, foot);
      } finally {
        busy(false);
      }
    };
    start.onclick = async () => {
      if (running) return;
      let got;
      try { got = canWriteFolder ? await pickFolder() : await pickFiles(); } catch (e) { return; }
      if (!got || !got.files.length) {
        if (got) window.toast('No maps there (.w3x, .w3m, .w3n).');
        return;
      }
      const action = select.value;
      const picked = got.files.map(file => ({ file, r: row(file) }));
      picked.dir = got.dir;
      list.replaceChildren(...picked.map(x => x.r.li));
      if (!ACTIONS[action].perMap) {
        foot.replaceChildren(el('span', { class: 'muted', text: picked.length + ' maps: ' + ACTIONS[action].label +
          ', one after the other.' }));
        await go(action, picked);
        return;
      }
      foot.replaceChildren(el('span', { class: 'muted', text: 'Reading the scripts of ' + picked.length + ' maps...' }));
      busy(true);
      stop = false;
      try {
        await readPacks(picked);
      } finally {
        busy(false);
      }
      const ready = picked.filter(x => x.params);
      if (!ready.length) {
        foot.replaceChildren(el('span', { class: 'muted', text: stop ? 'Stopped.' : 'No map can take a cheat pack.' }));
        return;
      }
      const same = el('button', { class: 'btn small', text: 'Same as the first map', onclick: () => {
        const n = ready.slice(1).filter(x => x.copyFrom(ready[0])).length;
        window.toast(n + ' of ' + (ready.length - 1) + ' maps took the first map\'s pack and activators.');
      } });
      const inject = el('button', { class: 'btn primary', text: 'Add the cheat packs', onclick: () => {
        foot.replaceChildren(el('span', { class: 'muted', text: ready.length + ' maps: ' +
          ACTIONS[action].label + ', one after the other.' }));
        go(action, picked);
      } });
      foot.replaceChildren(el('span', { class: 'muted grow', text: 'Pick the pack and the activators of each map.' }),
        ready.length > 1 ? same : null, inject);
    };
    return el('div', { class: 'card', id: 'queue', style: 'margin-top:14px' },
      el('h3', { text: 'Several maps' }),
      el('p', { class: 'muted', text: canWriteFolder ?
        'Run one action on every map of a folder: each result is saved next to its map. Fix, editor and port use ' +
        'the default options; the cheat pack and its activators are chosen per map.' :
        'Run one action on several maps: the results come back as one zip. Fix, editor and port use the default ' +
        'options; the cheat pack and its activators are chosen per map.' }),
      el('div', { class: 'row', style: 'gap:10px;align-items:center' }, select, start, cancel), list, foot);
  }

  window.addEventListener('DOMContentLoaded', () => {
    const welcome = document.getElementById('welcome');
    if (welcome && window.doctorWeb && !document.getElementById('queue')) welcome.appendChild(card());
  });
})();
