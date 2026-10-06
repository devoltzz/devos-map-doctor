// worker.js - the site's Web Worker (1.6; a module worker, Pyodide 314 has no classic one): Pyodide with the
// Doctor's engine, the same jobs as the exe's worker process. The page (ponte.js) sends:
//   {type: 'file', path, file}      a file the user picked (a map, a translation, an art package): mounted read-only at
//                                   /in/<n>/ (WORKERFS, no copy) and linked at `path` (/maps/<name> or /in/<name>)
//   {type: 'job', job}              a job (`job.id`, `job.task`, the params): one at a time, in order
//   {type: 'read', rid, path}       the bytes of a file the jobs wrote (a folder comes as a zip), for a download
//   {type: 'index', url}            the file name index (names.npz) next to the engine
//   {type: 'delete', rid, path}     a file the queue already saved, removed from memory
//   {type: 'zip', rid, paths, name} several files the jobs wrote, as one zip (the queue in Firefox)
// and gets {type: 'boot', label}, {type: 'ready'}, {type: 'boot_failed', message}, {type: 'event', event} (the job's
// progress, result or error, as JSON) and {type: 'read', rid, name, bytes | error}.

import { loadPyodide } from './pyodide/pyodide.mjs';
import { runWasi } from './wasi_mini.js';
import { windowsRules } from './fs_windows.js';

const ENGINE = '/home/pyodide/engine';
const GAME = '/home/pyodide/game';
let py = null;
let runJob = null;
let mounts = 0;
let queue = Promise.resolve();

function post(msg, transfer) { self.postMessage(msg, transfer || []); }

async function unpack(url, dir, required) {
  const r = await fetch(url);
  if (!r.ok) {
    if (required) throw new Error(url + ': ' + r.status);
    return false;
  }
  py.unpackArchive(await r.arrayBuffer(), 'zip', { extractDir: dir });
  return true;
}

async function boot() {
  post({ type: 'boot', label: 'Loading Python...' });
  py = await loadPyodide({ indexURL: new URL('pyodide/', import.meta.url).href, stdout: () => {}, stderr: () => {} });
  windowsRules(py.FS);             // the Windows rules for paths, which the engine was written for
  post({ type: 'boot', label: 'Loading numpy and Pillow...' });
  await py.loadPackage(['numpy', 'pillow'], { messageCallback: () => {} });
  post({ type: 'boot', label: 'Loading the engine...' });
  await unpack('engine.zip', ENGINE, true);
  // the game's data files (the pack of `casc_wc3`): without them the engine runs as on a PC without the game
  // (the release calls the variable WC3_GAME, the archive WC3_JOGO)
  if (await unpack('data/game_data.zip', GAME, false)) {
    py.runPython(`import os; os.environ['WC3_GAME'] = os.environ['WC3_JOGO'] = '${GAME}'`);
  }
  // pjass as WebAssembly (the port's gates, the GUI triggers' proof, the cheat packs): worker.py sends it the calls
  const pj = await fetch('pjass.wasm');
  if (pj.ok) {
    const mod = await WebAssembly.compile(await pj.arrayBuffer());
    self.runPjass = (args, files) => runWasi(mod, Array.from(args), files);
  }
  for (const d of ['/maps', '/in', '/out']) py.FS.mkdirTree(d);
  // the file name index, when the browser already keeps it (the page offers it once: check_update in ponte.js)
  try {
    const idx = 'caches' in self ? await caches.match('names.npz') : null;
    if (idx) py.FS.writeFile(ENGINE + '/names.npz', new Uint8Array(await idx.arrayBuffer()));
  } catch (e) { /* no cache in this browser */ }
  const glue = await (await fetch('worker.py')).text();
  py.FS.writeFile('/home/pyodide/doctor_worker.py', glue);
  py.runPython('import sys; sys.path.insert(0, "/home/pyodide")');
  const mod = py.pyimport('doctor_worker');
  runJob = mod.run;
  self.zipFolder = mod.zip_folder;
  self.zipFiles = mod.zip_files;
  post({ type: 'ready' });
}

function addFile(path, file) {
  const dir = '/in/' + (mounts++);
  py.FS.mkdirTree(dir);
  py.FS.mount(py.FS.filesystems.WORKERFS, { files: [file] }, dir);
  try { py.FS.unlink(path); } catch (e) { /* not there yet */ }
  py.FS.mkdirTree(path.slice(0, path.lastIndexOf('/')) || '/');
  py.FS.symlink(dir + '/' + file.name, path);
}

function readFile(rid, path) {
  try {
    let p = path;
    if (py.FS.isDir(py.FS.stat(path).mode)) {
      p = '/out/' + path.split('/').filter(Boolean).pop() + '.zip';
      self.zipFolder(path, p);
    }
    const bytes = py.FS.readFile(p);
    post({ type: 'read', rid, name: p.split('/').pop(), bytes }, [bytes.buffer]);
  } catch (e) {
    post({ type: 'read', rid, error: String(e && e.message || e) });
  }
}

const booted = boot().catch(e => { post({ type: 'boot_failed', message: String(e && e.message || e) }); throw e; });

self.onmessage = ev => {
  const m = ev.data;
  queue = queue.then(() => booted).then(() => {
    if (m.type === 'file') addFile(m.path, m.file);
    else if (m.type === 'read') readFile(m.rid, m.path);
    else if (m.type === 'delete') {
      try { py.FS.unlink(m.path); } catch (e) { /* already gone */ }
      post({ type: 'read', rid: m.rid, name: '', bytes: new Uint8Array(0) });
    } else if (m.type === 'zip') {
      try {
        self.zipFiles(py.toPy(m.paths), '/out/' + m.name);
        readFile(m.rid, '/out/' + m.name);
        py.FS.unlink('/out/' + m.name);
      } catch (e) { post({ type: 'read', rid: m.rid, error: String(e && e.message || e) }); }
    } else if (m.type === 'index') return fetch(m.url).then(r => {
      if (!r.ok) throw new Error(m.url + ': ' + r.status);
      return r.arrayBuffer();
    }).then(b => {
      py.FS.writeFile(ENGINE + '/names.npz', new Uint8Array(b));
      post({ type: 'event', event: JSON.stringify({ type: 'index_done' }) });
    }).catch(e => post({ type: 'event', event: JSON.stringify({ type: 'index_failed', message: String(e) }) }));
    else if (m.type === 'job') runJob(JSON.stringify(m.job), s => post({ type: 'event', event: s }));
  }).catch(() => {});
};
