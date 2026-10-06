// fila.js - the site's queue of several maps (1.6): one action (Fix map, Open in World Editor, Port to Reforged)
// on every map of a folder, one after the other, with the default options. In Chrome and Edge the folder itself is
// picked and each result is written next to its map, as the Windows program does; in a browser that cannot write a
// folder (Firefox) the maps are picked as files and the results come back as one zip at the end. Runs through
// window.doctorWeb (ponte.js); uses the page's el(), toast() and mb() (app.js).
'use strict';

(() => {
  const ACTIONS = {
    fix: { label: 'Fix map', params: () => ({ options: null, extras: {} }) },
    editor: { label: 'Open in World Editor', params: () => ({ options: null, extras: {} }) },
    port: { label: 'Port to Reforged', params: () => ({ packages: [], memory: true }) },
  };
  const MAP = /\.w3[xmn]$/i;
  const OURS = /_(fixed|editor|reforged)( \(\d+\))?\.w3[xmn]$/i;   // what an earlier run wrote: not a map to treat
  const canWriteFolder = typeof window.showDirectoryPicker === 'function';
  let running = false;
  let stop = false;

  async function exists(dir, name) {
    try { await dir.getFileHandle(name); return true; } catch (e) { return false; }
  }

  // `<map>_fixed.w3x` next to the map, never over a file: `... (2).w3x`, as the Windows program does
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
    nothing: ['info', 'Nothing to do'],
    failed: ['bad', 'Stopped'], skipped: ['warn', 'Skipped'], cancelled: ['info', 'Cancelled'] };

  function row(file) {
    const state = el('span', { class: 'badge', text: 'Waiting' });
    const note = el('div', { class: 'faint', text: window.mb ? window.mb(file.size) : '' });
    const li = el('li', { class: 'step' }, el('div', { class: 'grow' }, el('div', { class: 'mono', text: file.name }),
      note), state);
    return { li, set(kind, text) {
      const b = BADGE[kind] || ['info', kind];
      state.className = 'badge ' + b[0];
      state.textContent = b[1];
      if (text !== undefined) note.textContent = text;
    }, note(text) { note.textContent = text; } };
  }

  async function runQueue(action, picked, list, foot) {
    const W = window.doctorWeb;
    const zipped = [];
    let done = 0;
    for (const { file, r } of picked) {
      if (stop) { r.set('cancelled', ''); continue; }
      if (file.size > W.sizeLimit) {
        r.set('skipped', 'Above ' + Math.round(W.sizeLimit / 1048576) + ' MB: use the Windows program.');
        continue;
      }
      r.set('running', 'Starting...');
      const path = W.addPicked(file, '/maps');
      const ev = await W.run(action, Object.assign({ map: path }, ACTIONS[action].params()), label => r.note(label));
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
      r.set(kind, saved.length ? (picked.dir ? 'Saved ' : 'In the zip: ') + saved.join(', ') : 'Nothing was written.');
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
    start.onclick = async () => {
      if (running) return;
      let got;
      try { got = canWriteFolder ? await pickFolder() : await pickFiles(); } catch (e) { return; }
      if (!got || !got.files.length) {
        if (got) window.toast('No maps there (.w3x, .w3m, .w3n).');
        return;
      }
      running = true;
      stop = false;
      start.disabled = true;
      select.disabled = true;
      cancel.classList.remove('hidden');
      const picked = got.files.map(file => ({ file, r: row(file) }));
      picked.dir = got.dir;
      list.replaceChildren(...picked.map(x => x.r.li));
      foot.replaceChildren(el('span', { class: 'muted', text: picked.length + ' maps: ' +
        ACTIONS[select.value].label + ', one after the other.' }));
      try {
        await runQueue(select.value, picked, list, foot);
      } finally {
        running = false;
        start.disabled = false;
        select.disabled = false;
        cancel.classList.add('hidden');
      }
    };
    return el('div', { class: 'card', id: 'queue', style: 'margin-top:14px' },
      el('h3', { text: 'Several maps' }),
      el('p', { class: 'muted', text: canWriteFolder ?
        'Run one action on every map of a folder, with the default options: each result is saved next to its map.' :
        'Run one action on several maps, with the default options: the results come back as one zip.' }),
      el('div', { class: 'row', style: 'gap:10px;align-items:center' }, select, start, cancel), list, foot);
  }

  window.addEventListener('DOMContentLoaded', () => {
    const welcome = document.getElementById('welcome');
    if (welcome && window.doctorWeb && !document.getElementById('queue')) welcome.appendChild(card());
  });
})();
